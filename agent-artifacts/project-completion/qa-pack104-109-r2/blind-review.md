# Blind review before keys / manifests / R1 verdict

Input read: pack-104-109-r2/blind-log-cases.json only (apart from directory inventory). Recorded before reading keyed cases or prior QA.

- TC-108 strongest B: 100,000 complete samples, 100 MB, all-week coverage. Runner-up D: about 59,524 full examples in the final hour, about 59.5 MB, but it loses the other 167 hours and fails required all-week representativeness. A is 10 GB and violates the hard cap. C preserves an exact count but zero diagnostic examples.
- TC-109 strongest A: 500 full examples, 500 KB, all-week coverage. Runner-up B: 5 complete samples, only 5 KB, but below the 100-example floor. D retains about 3 final-hour examples, loses coverage and also misses the floor. C retains none.

Blind uniqueness: yes for both. C and D are conceptually distinct count-versus-detail and retention-versus-coverage mistakes. C is nevertheless directly ruled out by the explicit minimum of full examples; D is directly ruled out by the explicit all-week requirement. Whether these qualify as sufficiently strong distractors remains pending source and rubric review.
