# To DO

# Functionality
	- Create executable
		- Dependency structure
		- Fix virtual environment config
		- requirements.txt
		- refine readme
	
	- Publish logs message to Teams?
	
		
# GUI		
	- Transfer status progress bar
		- Replace/Add additional progress bar when operations are running that map to actual transfer progress
		
		
# Validation
	- Force untoggle nvram_reset and/or nvram_demo_reset if both selection boxes are selected
		- Prevent second selection until first is unselected
		
		
# Optimisations
	- Session generation
		- Preserve session in pipeline?
		
	
# Debug
	- Log output review and restructure
		- Logger/Debug review
		- Cohesive logger level rewrite
		- Additional colour scheme/labels?
	
[	
	'DEBUG': "\x1b[34m",    # Blue
	'INFO': "\x1b[32m",     # Green
	'WARNING': "\x1b[33m",  # Yellow
	'ERROR': "\x1b[31m",    # Red
	'CRITICAL': "\x1b[41m", # Red background
]
	
https://stackoverflow.com/questions/384076/how-can-i-color-python-logging-output/56944256#56944256
	
# Bugs
	- NVRAM Resets
		- Currently only deletes all files
			- Possible that folder in NVRAM will cause issues