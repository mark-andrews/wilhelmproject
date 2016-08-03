#/usr/bin/zsh
mkdir -p static/ans/css

lessc --include-path=.:..:../../apps/front/less/:../../apps/front/less/bootstrap/ less/ans.less > static/ans/css/ans.css
