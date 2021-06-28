TO DO:
1. fix static file location so html templates can access css and image files.  

DONE:
1. abstract functions in anomaly.py, incentivized.py, and similarity.py by making an abstract parent class called detection_algorithms that will have shared functions.  
2. abstract views.plot() into one function called three times for similarity, anomaly, and incentivized scoring. 
3. Have matplotlib show graphs to console and view.  
4. Lookup normalization (about what consitutes new relations) and update/migrate models and file_to_database to include the bool 'incentivized' (similar to duplicate). Also update relation documentation.  
