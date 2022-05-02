source .venv/bin/activate;
python -m spacy download ro_core_news_lg
python export-common-lexicon.py --db-server $1 --db-name $2 --user $3 --password $4 --output-dir ./common-lexii
deactivate;
zip -r common-lexii.zip common-lexii;
mv -f common-lexii.zip /var/export/;
rm -rf ./common-lexii
