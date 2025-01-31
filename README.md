# Data_Transfer
Transfer data from Local Directory through API

1. Create virtual environtment.\
    python -m venv virtenv

    using powershell activate the Activate.ps1 under the scripts folder\
    secLabel\Scripts\Activate.ps1
    
2. pip install the library need in requirement.txt\
    pip install -r requirements.txt

3. Build application\
    pip pyinstaller --noconsole app_name.py
4. Browse directory to read CSV file.
5. Click start to read latest CSV file.
6. CSV data will be posted to your RestApi url.
7. The app will always running and waiting for the new csv file.
8. App also have logs to show every CSV file processed and automatically delete every 7 days.