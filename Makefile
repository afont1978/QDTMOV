install:
	python -m pip install -r requirements.txt

app:
	python -m streamlit run app.py

test:
	python -m pytest -q

api:
	python -m uvicorn mobility_os.api.fastapi_app:app --app-dir src --reload
