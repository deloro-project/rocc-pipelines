source .venv/bin/activate;
python export-lexicon.py --db-server $1 --db-name $2 --user $3 --password $4 --output-dir ./lexii
deactivate;
zip -r lexii.zip lexii;
mv -f lexii.zip /var/export/;
rm -rf ./lexii
