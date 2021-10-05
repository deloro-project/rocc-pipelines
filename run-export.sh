source .venv/bin/activate;
python export-annotations.py --db-server $1 --db-name $2 --user $3 --password $4;
deactivate;
zip -r annotations.zip export;
mv -f annotations.zip /var/export/
