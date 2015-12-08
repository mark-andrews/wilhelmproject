#/usr/bin/zsh
mkdir -p static/bartlett/css

lessc --include-path=.:..:../../apps/front/less/:../../apps/front/less/bootstrap/ less/bartlett.less > static/bartlett/css/bartlett.css
