"""Export-only dense, eval, batch-one adapters. Weights are copied unchanged.
Math follows packaged fastpitch_layers.py / jit_forward_model.py.
"""
import torch
from torch import nn
from torch.nn import functional as F

def leaf(m):
    name=m.original_name
    if name in ('Linear','NonDynamicallyQuantizableLinear'): n=nn.Linear(m.in_features,m.out_features,m.bias is not None)
    elif name=='Embedding': n=nn.Embedding(m.num_embeddings,m.embedding_dim,padding_idx=m.padding_idx)
    elif name=='LayerNorm': n=nn.LayerNorm(tuple(m.normalized_shape),eps=m.eps)
    elif name=='Conv1d': n=nn.Conv1d(m.in_channels,m.out_channels,tuple(m.kernel_size),tuple(m.stride),tuple(m.padding),tuple(m.dilation),m.groups,m.bias is not None)
    else: raise ValueError(name)
    n.load_state_dict(m.state_dict());n.eval();return n

class Attention(nn.Module):
    def __init__(self,m):
        super().__init__();assert m.batch_first and m.bias_k is None and m.bias_v is None and not m.add_zero_attn
        self.weight=nn.Parameter(m.in_proj_weight.detach().clone());self.bias=nn.Parameter(m.in_proj_bias.detach().clone())
        self.out=leaf(m.out_proj);self.heads=m.num_heads;self.dim=m.embed_dim//m.num_heads
    def forward(self,x,mask):
        b,t,_=x.shape
        q,k,v=F.linear(x,self.weight,self.bias).chunk(3,dim=-1)
        q=q.reshape(b,t,self.heads,self.dim).transpose(1,2)
        k=k.reshape(b,t,self.heads,self.dim).transpose(1,2)
        v=v.reshape(b,t,self.heads,self.dim).transpose(1,2)
        scores=(q*(self.dim**-0.5))@k.transpose(-1,-2)
        if mask is not None:scores=scores.masked_fill(mask[:,None,None,:],float('-inf'))
        y=(scores.softmax(-1)@v).transpose(1,2).reshape(b,t,self.heads*self.dim)
        return self.out(y)

class Block(nn.Module):
    def __init__(self,m):
        super().__init__();self.att=Attention(m.self_attn);self.n1=leaf(m.norm1);self.n2=leaf(m.norm2)
        self.c1=leaf(m.conv1);self.c2=leaf(m.conv2);self.linear=m.use_linear;self.pitch=m.pitch_pred
        assert not m.style_norm and not m.conditional_cross_attention
    def forward(self,x,mask=None):
        x=self.n1(x+self.att(x,mask))
        if not self.linear:x=x.transpose(1,2)
        y=self.c2(F.relu(self.c1(x)))
        if self.pitch:
            y=F.relu(y);x=(x+y)+y
        else:x=x+y
        if not self.linear:x=x.transpose(1,2)
        return self.n2(x)

class Transformer(nn.Module):
    def __init__(self,m):
        super().__init__();self.register_buffer('pe',m.pos_encoder.pe.detach().clone());self.scale=nn.Parameter(m.pos_encoder.scale.detach().clone())
        self.layers=nn.ModuleList([Block(x) for x in m.layers.children()]);self.norm=leaf(m.norm)
    def forward(self,x,mask=None):
        x=x+(self.scale*self.pe[:x.shape[1]]).transpose(0,1)
        for layer in self.layers:x=layer(x,mask)
        return self.norm(x)

class Predictor(nn.Module):
    def __init__(self,m,pitch=False):
        super().__init__();self.pitch=pitch;self.emb=leaf(m.embedding);self.speaker=leaf(m.speaker_embedding);self.lin=leaf(m.lin)
        self.transformer=Transformer(m.transformer);self.types=leaf(m.type_embedding) if m.utt_type_emb else None
    def forward(self,sequence,speaker_ids,mask,type_ids):
        x=self.emb(sequence)+self.speaker(speaker_ids).unsqueeze(1).repeat(1,sequence.shape[1],1)
        if self.types is not None:x=x+self.types(type_ids)
        y=self.lin(self.transformer(x,mask))
        return y.transpose(1,2) if self.pitch else y.squeeze(-1)

class Encoder(nn.Module):
    def __init__(self,m):
        super().__init__();self.emb=leaf(m.embedding);self.sp=leaf(m.speaker_embedding);self.enc=Transformer(m.encoder);self.pitch=leaf(m.pitch_proj);self.strength=m.pitch_strength
        assert m.pitch_emb_type=='default'
    def forward(self,sequence,speaker_ids,mask,pitch):
        x=self.enc(self.emb(sequence),mask)+self.sp(speaker_ids).unsqueeze(1).repeat(1,sequence.shape[1],1)
        return x+self.pitch(pitch).transpose(1,2)*self.strength

class Decoder(nn.Module):
    def __init__(self,m):
        super().__init__();d=m.decoder;self.register_buffer('pe',d.pos_encoder.pe.detach().clone());self.scale=nn.Parameter(d.pos_encoder.scale.detach().clone())
        self.pre=nn.ModuleList([Block(x) for x in d.pre_vanilla_layers.children()]);self.short=nn.ModuleList([Block(x) for x in d.shorten_layers.children()]);self.post=nn.ModuleList([Block(x) for x in d.post_vanilla_layers.children()]);self.factor=d.shorten_factor
        pool=d.downsample.avg_pool
        self.pool=nn.AvgPool1d(pool.kernel_size,pool.stride,pool.padding,pool.ceil_mode,pool.count_include_pad)
        self.up=leaf(d.upsample.proj);self.dim=d.upsample.dim;self.norm=leaf(d.norm);self.lin=leaf(m.lin)
    def forward(self,x):
        length=x.shape[1];x=x+(self.scale*self.pe[:length]).transpose(0,1)
        for block in self.pre:x=block(x)
        x=F.pad(x,(0,0,0,(self.factor-length%self.factor)%self.factor))
        down=self.pool(x.transpose(1,2)).transpose(1,2)
        # Original calls each shortened layer on the SAME downsampled tensor.
        # Preserve this behavior, do not "fix" it into a sequential transformer.
        for block in self.short:y=block(down)
        y=self.up(y).reshape(x.shape[0],-1,self.dim)
        x=(x+y)[:,:length]
        for block in self.post:x=block(x)
        return self.lin(self.norm(x)).transpose(1,2)

class Spectral(nn.Module):
    def __init__(self,c):
        super().__init__();self.backbone=c.vocoder.backbone;self.out=c.vocoder.head.out
    def forward(self,mel):return self.out(self.backbone(mel)).transpose(1,2)
