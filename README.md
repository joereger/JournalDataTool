JournalDataTool Instructions

Overview:
This project aims to migrate historical data from legacy MyISAM MySQL formats for blog and mythredz into Trello, JSON, and CSV formats for future usage. The scripts in this project process and transform data from old MySQL databases, push it to Trello boards, and export it to easily accessible JSON and CSV files.

Prerequisites:
1. Python 3.10.9 or later
2. MySQL 5.7 (for mounting legacy MyISAM tables)
3. Python virtual environment
4. Required Python libraries (install using pip):
   - mysql-connector-python
   - requests
   - termcolor
   - ratelimit

Setup:
1. Create a Python virtual environment:
   python -m venv venv
   source venv/bin/activate  # On Windows, use: venv\Scripts\activate

2. Install required libraries:
   pip install mysql-connector-python requests termcolor ratelimit

3. Ensure you have the 'api_keys_and_tokens.txt' file in the project root directory with the necessary API keys and tokens.

File Structure:
- api_keys_and_tokens.txt: Configuration file for API keys and tokens
- blog_csvjson_utils.py: Utility functions for CSV and JSON operations (blog data)
- blog_to_csvjson.py: Script to export blog data to CSV and JSON
- blog_to_trello.py: Script to push blog data to Trello
- blog_trello_utils.py: Utility functions for Trello operations (blog data)
- mythredz_csvjson_utils.py: Utility functions for CSV and JSON operations (mythredz data)
- mythredz_to_csvjson.py: Script to export mythredz data to CSV and JSON (also combines with blog data)
- mythredz_to_trello.py: Script to push mythredz data to Trello
- mythredz_trello_utils.py: Utility functions for Trello operations (mythredz data)
- mysql_dump.py: Script to export MySQL data to JSON and CSV
- exported_data/: Directory containing the final output files
- mysql_data_exported/: Directory containing exported MySQL data
- source_data/: Directory containing source MyISAM tables

Example api_keys_and_tokens.txt (in root)

trello_api_key=xxxxxxxx
trello_token=xxxxxxx
trello_test_board_id=xxxxxxxx

Usage Instructions:
1. Mount the MyISAM tables from the source_data folder into a MySQL 5.7 database.
2. Repair the mounted MyISAM tables if necessary.
3. Run mysql_dump.py to export the MySQL data to JSON and CSV:
   python mysql_dump.py

4. Run blog_to_trello.py to push blog data to Trello:
   python blog_to_trello.py

5. Run mythredz_to_trello.py to push mythredz data to Trello:
   python mythredz_to_trello.py

6. Run blog_to_csvjson.py to archive blog data in a generic format:
   python blog_to_csvjson.py

7. Run mythredz_to_csvjson.py to archive mythredz data and combine it with blog data:
   python mythredz_to_csvjson.py

Note: If you only need the final output of this project, look in the exported_data directory. This contains the combined and processed data in JSON and CSV formats.

Maintenance:
These scripts are generally not intended for regular use. They were created for a one-time migration of historical data. However, if you need to access additional data from the MyISAM tables, you may need to run these scripts again.

Troubleshooting:
- If you encounter any issues with MySQL connections, ensure that the credentials in mysql_dump.py are correct and that your MySQL server is running.
- For Trello-related issues, check that your API keys and tokens in api_keys_and_tokens.txt are valid and have the necessary permissions.
- If you run into any Python errors, make sure you're using Python 3.10.9 or later and that all required libraries are installed in your virtual environment.

For any further assistance or questions about this project, please refer to the original project documentation or contact the project maintainer.
