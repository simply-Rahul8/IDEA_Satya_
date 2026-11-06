import os, sys, json
os.environ["SATYA_LLM"]="mock"; sys.path.insert(0, os.getcwd())
from engine import api
from engine.models import *
from engine.export.csv_export import export_csv
from engine.translate.service import translate_pack
rs=api.load_ruleset()
truth=ProductTruth(product_name="=HYPERLINK(\"http://evil\",\"x\") Glow Serum", size="30 ml", how_to_use="Apply two drops.", warnings="External use only.", storage="Store cool.", claims=[Claim(id="c1", text="Hydrating", status=ClaimStatus.CONFIRMED, evidence=Evidence(type=EvidenceType.BRAND_DECLARATION))])
rep=api.generate_verified_pack(truth, tone="professional", ruleset=rs)
st=api.approval_status(rep.pack, truth); print("approvable", st.approvable, st.blockers[:4])
try:
    r=export_csv(rep.pack, truth); print("export ok", r.filename); print(r.content.decode('utf-8-sig')[:400]); print(r.audit.to_json()[:300])
except Exception as e: print("export", type(e).__name__, str(e)[:300])
hi=translate_pack(rep.pack, truth)
print("hindi verifier_passed:", hi.verifier_passed)
for s in hi.section("title").sentences: print("hi title:", s.text.encode('unicode_escape')[:80], len(s.flags))
print("hi disclaimer present:", any("legal" == s.type.value for s in hi.section("warnings_storage").sentences))
try:
    r=export_csv(hi, truth); print("HINDI export allowed w/o verification? ->", r.filename)
except Exception as e: print("hindi export blocked:", str(e)[:150])
print("---- verify hindi")
try:
    vr=api.verify_pack(hi, truth, ruleset=rs); print("pass2", vr.pass2_completed, "verified", vr.pack.verifier_passed, "approvable", api.approval_status(vr.pack, truth).approvable)
    print("hi flags after verify", [(f.rule_id,f.severity.value) for sec in vr.pack.sections for s in sec.sentences for f in s.flags][:5])
    r=export_csv(vr.pack, truth); print("hindi export ok")
except Exception as e: print("hindi after verify:", type(e).__name__, str(e)[:200])
