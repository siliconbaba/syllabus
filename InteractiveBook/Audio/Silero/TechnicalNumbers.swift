import Foundation

enum TechnicalNumbers {
    static let units=["", "один","два","три","четыре","пять","шесть","семь","восемь","девять","десять","одиннадцать","двенадцать","тринадцать","четырнадцать","пятнадцать","шестнадцать","семнадцать","восемнадцать","девятнадцать"]
    static let tens=["","","двадцать","тридцать","сорок","пятьдесят","шестьдесят","семьдесят","восемьдесят","девяносто"]
    static let hundreds=["","сто","двести","триста","четыреста","пятьсот","шестьсот","семьсот","восемьсот","девятьсот"]
    static func form(_ n:Int64,_ words:[String])->String {
        let n=Int(n%100);if (11...14).contains(n){return words[2]};return n%10==1 ? words[0] : (2...4).contains(n%10) ? words[1]:words[2]
    }
    static func triple(_ n:Int,_ female:Bool)->[String] {
        var out:[String]=[];if n>=100{out.append(hundreds[n/100])};let r=n%100
        if r>=20{out.append(tens[r/10])}
        let u=r<20 ? r:r%10
        if u>0{out.append(female && u==1 ? "одна":female && u==2 ? "две":units[u])};return out
    }
    static func integer(_ digits:String,female:Bool=false)->String {
        // Long IDs and leading zeroes are spelled digit-by-digit, never truncated.
        if digits.count>1 && digits.first=="0" {return digits.map{integer(String($0))}.joined(separator:" ")}
        guard let n=Int64(digits), n<1_000_000_000_000_000 else{return digits.map{integer(String($0))}.joined(separator:" ")}
        if n==0{return "ноль"};var out:[String]=[]
        let groups:[(Int64,[String],Bool)]=[(1_000_000_000_000,["триллион","триллиона","триллионов"],false),(1_000_000_000,["миллиард","миллиарда","миллиардов"],false),(1_000_000,["миллион","миллиона","миллионов"],false),(1000,["тысяча","тысячи","тысяч"],true)]
        for (scale,nouns,gender) in groups {let g=n/scale%1000;if g>0{out += triple(Int(g),gender);out.append(form(g,nouns))}}
        out += triple(Int(n%1000),female);return out.joined(separator:" ")
    }
    static func number(_ value:String,female:Bool=false)->String {
        let parts=value.replacingOccurrences(of:",",with:".").components(separatedBy:".")
        if parts.count==1{return integer(value,female:female)}
        let precision=parts[1].count;let names=[1:["десятая","десятых"],2:["сотая","сотых"],3:["тысячная","тысячных"],4:["десятитысячная","десятитысячных"],5:["стотысячная","стотысячных"],6:["миллионная","миллионных"]]
        guard let denominator=names[precision],let fraction=Int64(parts[1]),let whole=Int64(parts[0]) else{return parts.map{integer($0)}.joined(separator:" точка ")}
        let singular=whole%10==1 && whole%100 != 11
        let fSingular=fraction%10==1 && fraction%100 != 11
        return integer(String(whole),female:true)+(singular ? " целая ":" целых ")+integer(String(fraction),female:true)+" "+denominator[fSingular ? 0:1]
    }
    static func genitive(_ spoken:String)->String {
        let map=["ноль":"нуля","один":"одного","одна":"одной","два":"двух","две":"двух","три":"трёх","четыре":"четырёх","пять":"пяти","шесть":"шести","семь":"семи","восемь":"восьми","девять":"девяти","десять":"десяти","одиннадцать":"одиннадцати","двенадцать":"двенадцати","тринадцать":"тринадцати","четырнадцать":"четырнадцати","пятнадцать":"пятнадцати","шестнадцать":"шестнадцати","семнадцать":"семнадцати","восемнадцать":"восемнадцати","девятнадцать":"девятнадцати","двадцать":"двадцати","тридцать":"тридцати","сорок":"сорока","пятьдесят":"пятидесяти","шестьдесят":"шестидесяти","семьдесят":"семидесяти","восемьдесят":"восьмидесяти","девяносто":"девяноста","сто":"ста","двести":"двухсот","триста":"трёхсот","четыреста":"четырёхсот","пятьсот":"пятисот","шестьсот":"шестисот","семьсот":"семисот","восемьсот":"восьмисот","девятьсот":"девятисот","тысяча":"тысячи","тысячи":"тысяч","миллион":"миллиона","миллиона":"миллионов","миллиард":"миллиарда","миллиарда":"миллиардов","триллион":"триллиона","триллиона":"триллионов","целая":"целой","десятая":"десятой","сотая":"сотой","тысячная":"тысячной","десятитысячная":"десятитысячной","стотысячная":"стотысячной","миллионная":"миллионной"]
        return spoken.split(separator:" ").map{map[String($0)] ?? String($0)}.joined(separator:" ")
    }
    static func version(_ value:String)->String {value.split(separator:".").map{integer(String($0))}.joined(separator:" точка ")}
    static func year(_ value:String,_ noun:String)->String {
        let n=Int(value)!;let small=[1:"первый",2:"второй",3:"третий",4:"четвёртый",5:"пятый",6:"шестой",7:"седьмой",8:"восьмой",9:"девятый",10:"десятый",11:"одиннадцатый",12:"двенадцатый",13:"тринадцатый",14:"четырнадцатый",15:"пятнадцатый",16:"шестнадцатый",17:"семнадцатый",18:"восемнадцатый",19:"девятнадцатый",20:"двадцатый",30:"тридцатый",40:"сороковой",50:"пятидесятый",60:"шестидесятый",70:"семидесятый",80:"восьмидесятый",90:"девяностый",100:"сотый",200:"двухсотый",300:"трёхсотый",400:"четырёхсотый",500:"пятисотый",600:"шестисотый",700:"семисотый",800:"восьмисотый",900:"девятисотый",1000:"тысячный",2000:"двухтысячный"]
        let last = n%100 != 0 ? (n%100<20 || n%10==0 ? n%100:n%10) : (n%1000 != 0 ? n%1000:n)
        guard var ordinal=small[last] else{return integer(value)+" "+noun}
        if noun=="году"{ordinal=ordinal=="третий" ? "третьем":String(ordinal.dropLast(2))+"ом"}
        if noun=="года"{ordinal=ordinal=="третий" ? "третьего":String(ordinal.dropLast(2))+"ого"}
        return (n>last ? integer(String(n-last))+" ":"")+ordinal+" "+noun
    }
}
