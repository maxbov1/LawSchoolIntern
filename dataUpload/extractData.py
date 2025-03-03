import pandas as pd
import numpy as np
import re
import logging

def extract(category, data,cols=None):
    '''
    This function accepts two arguements : the category or source of the data, and the data (pd.Dataframe)
    This function is responsible for extracting the data in our given csv based upon preconcieved notions of what features will be included in each file. The function returns a cleaned, pandas df indexed on SID. 
    '''
    if category == 'additional':

        '''
            currently setup to try and extract anticipated columns from Amy's data.
        '''
        try: 
            data = data.loc[1:,["SID", "Which bar review","22-Feb"]]

            data.columns = ["SID", "bar_review", "percent_completion"]
            
            extract_first_percent = lambda x: int(re.search(r"(\d+)%", str(x)).group(1)) if re.search(r"(\d+)%", str(x)) else None
            
            data['review_completion'] = data['percent_completion'].apply(extract_first_percent)
            
            '''
                we need to determine what cases / students  ( missing data ) we want to support in our database.
            '''
            data = data.dropna(subset=["SID"])
            
            data.drop(columns=["percent_completion"], inplace=True)
            
            data['SID'] = data['SID'].astype(int)
            
            #data = data.set_index('SID') 
            
            logging.info(f"additional data: {data}") 
            logging.info(f"additional dytpes : {data.dtypes}")
            return data 
        except Exception as e:
            
            logging.exception(f"Unexpected error: {e}")

    elif category == 'registrar':
        pass
    
    elif category == 'admissions':
        
        try:
            data.columns = data.columns.str.strip()

            admissions_cleaned = data.loc[:, ['First', 'Last', 'SID','LSAT', 'Applicant GPA']]
            
            admissions_cleaned.columns = ["firstname", "lastname", "SID","lsat_score", "undergrad_gpa"] 
            
            admissions = admissions_cleaned.dropna(subset=['SID'])
            
            admissions['SID'] = admissions['SID'].astype(int)

            admissions['lsat_score'] = admissions['lsat_score'].apply(lambda x: int(x) if pd.notna(x) and np.isfinite(x) else x)

            logging.info(f"admissions data types: {admissions.dtypes}")

            #admissions = admissions.set_index('SID')
            
            logging.info(f"admissions data: {admissions}")
            return admissions
        except KeyError as e:
            
            logging.error(f"Missing column in the data: {e}")
        
        except Exception as e:
            
            logging.exception(f"Unexpected error: {e}")

