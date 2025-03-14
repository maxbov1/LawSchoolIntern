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

            data['SID'] = data['SID'].astype(str).str.zfill(8)

            logging.info(f"additional data: {data}") 
            logging.info(f"additional dytpes : {data.dtypes}")
            return data 
        except Exception as e:
            
            logging.exception(f"Unexpected error: {e}")
    
    elif category == 'bar':
        
        bar_clean = data.loc[:,["SID","FirstTimeJuris"]]
        
        bar_clean['result'] = bar_clean['FirstTimeJuris'].str[2:]

        bar_clean['result'] = bar_clean['result'].str.lower()
  
        bar_clean['juris'] = bar_clean['FirstTimeJuris'].str[:2]
        
        bar_clean.drop(columns=['FirstTimeJuris'], inplace=True) 
        
        #bar['SID'] = bar['SID'].astype(str).str.zfill(8)

        bar_clean = bar_clean.dropna(axis=0)
        
        return bar_clean
        
        logging.info(f"bar data: {bar_clean}")
        
        logging.info(f"bar dytpes : {bar_clean.dtypes}")

    elif category == 'registrar':
        
        registrar = data.loc[:,["Degree GPA", "Student ID","Full Name","Student NETID","Degree Conferral Date"]]
        
        registrar.columns = ["law_gpa", "SID","Full Name","NetID","grad_date"]

        registrar[['lastname', 'First Middle']] = registrar['Full Name'].str.split(',', expand=True)

        registrar['firstname'] = registrar['First Middle'].str.split().str[0]

        registrar = registrar.drop(columns=["Full Name", "First Middle"])
        
        registrar['SID'] = registrar['SID'].astype(str).str.zfill(8)

        registrar = registrar.dropna(subset=['SID'])
    
        return registrar

        logging.info(f"registrar data: {registrar}")

        logging.info(f"registrar dytpes : {registrar.dtypes}")
    
    elif category == 'admissions':
        
        try:
            data.columns = data.columns.str.strip()

            admissions_cleaned = data.loc[:, ['SID','LSAT', 'Applicant GPA']]
            
            admissions_cleaned.columns = ["SID","lsat_score", "undergrad_gpa"] 
            
            admissions = admissions_cleaned.dropna(subset=['SID'])
            
            admissions['SID'] = admissions['SID'].astype(int)

            admissions['SID'] = admissions['SID'].astype(str).str.zfill(8)
            
            admissions['lsat_score'] = admissions['lsat_score'].apply(lambda x: int(x) if pd.notna(x) and np.isfinite(x) else x)

            logging.info(f"admissions data types: {admissions.dtypes}")

            #admissions = admissions.set_index('SID')
            
            logging.info(f"admissions data: {admissions}")
            return admissions
        except KeyError as e:
            
            logging.error(f"Missing column in the data: {e}")
        
        except Exception as e:
            
            logging.exception(f"Unexpected error: {e}")

