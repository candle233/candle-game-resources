"""Generate a ZCode user-hook fragment without editing any user/global configuration."""
from pathlib import Path
import argparse, sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT, save

def fragment(root,python):
    events={}
    for event in ('SessionStart','PreToolUse','PostToolUse','Stop'):
        events[event]=[{'hooks':[{'type':'process','command':str(python),'args':['-I',str(root/'harness/scripts/hooks.py'),'--root',str(root),'--client','zcode'],'enabled':True,'timeoutMs':8000}]}]
    return {'hooks':{'enabled':True,'timeoutMs':8000,'maxOutputBytes':32768,'events':events}}

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=ROOT);p.add_argument('--adapter',choices=['zcode'],required=True)
    a=p.parse_args(argv);root=a.root.resolve();out=root/'Artifacts/harness/zcode-user-hooks.json'
    save(out,fragment(root,Path(sys.executable).resolve()))
    print('Generated: '+str(out));print('Review and MERGE hook event arrays into ~/.zcode/cli/config.json. Do not replace existing user settings. Restart the session.');return 0
if __name__=='__main__':raise SystemExit(main())
