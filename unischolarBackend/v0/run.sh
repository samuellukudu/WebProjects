# python -m spacy download en_core_web_sm

python main.py --query "top AI startups" --search-results ai_search.csv --verified-companies ai_companies.csv --delay 2 --log-level DEBUG

# python main.py --query "top AI startups" --delay 0.5 --log-level INFO --proxies "http://proxy1:port,http://proxy2:port"

# python -m unischolar.main search "universities in Germany computer science" --max-results 5