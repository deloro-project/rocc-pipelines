source .venv/bin/activate;
pip install -r requirements.txt
python -m spacy download ro_core_news_lg
python export-lexicon.py --db-server $1 --db-name $2 --user $3 --password $4 --output-dir ./lexii
deactivate;
zip -r lexii.zip lexii;
mv -f lexii.zip /var/export/;
rm -rf ./lexii
