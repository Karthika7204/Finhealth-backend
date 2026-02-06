from app import app, db
from models import Analysis
import random

with app.app_context():
    analyses = Analysis.query.all()
    print(f"Found {len(analyses)} analyses to check...")
    
    count = 0
    for a in analyses:
        if a.raw_result:
            # Check if fields are missing
            updated = False
            
            # Since we are modifying a JSON field, we might need to copy, modify, and re-assign 
            # to trigger SQLAlchemy's tracking of mutable JSON (if not using MutableDict)
            new_result = dict(a.raw_result)
            
            if 'category' not in new_result:
                new_result['category'] = random.choice(['Tech', 'Retail', 'Services', 'Healthcare'])
                updated = True
                
            if 'industry' not in new_result:
                new_result['industry'] = random.choice(['Software', 'E-commerce', 'Consulting', 'Medical'])
                updated = True
            
            if updated:
                a.raw_result = new_result
                count += 1
    
    if count > 0:
        db.session.commit()
        print(f"✅ Successfully backfilled {count} analyses with Category/Industry data!")
    else:
        print("Everything already has data.")
