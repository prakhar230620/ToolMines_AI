from datetime import datetime, timedelta
from config.database import db
from bson import ObjectId

class UserStats:
    @staticmethod
    def get_total_users():
        """Get total number of registered users"""
        return db.users.count_documents({})

    @staticmethod
    def get_active_users(days=30):
        """Get number of users who were active in the last N days"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        return db.users.count_documents({"last_login": {"$gte": cutoff_date}})

    @staticmethod
    def get_new_users(days=30):
        """Get number of new users registered in the last N days"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        return db.users.count_documents({"created_at": {"$gte": cutoff_date}})

    @staticmethod
    def get_user_growth():
        """Get user growth statistics starting from January 2025"""
        start_date = datetime(2025, 1, 1)
        current_date = datetime.utcnow()
        months_data = []
        labels = []

        while start_date <= current_date:
            end_date = datetime(start_date.year, start_date.month + 1, 1) if start_date.month < 12 else datetime(start_date.year + 1, 1, 1)
            count = db.users.count_documents({
                "created_at": {
                    "$gte": start_date,
                    "$lt": end_date
                }
            })
            month_label = start_date.strftime("%B %Y")
            months_data.append(count)
            labels.append(month_label)
            
            # Move to next month
            if start_date.month == 12:
                start_date = datetime(start_date.year + 1, 1, 1)
            else:
                start_date = datetime(start_date.year, start_date.month + 1, 1)

        return {
            "labels": labels,
            "values": months_data
        }

    @staticmethod
    def get_user_activity():
        """Get user activity statistics for the last 7 days"""
        current_date = datetime.utcnow()
        daily_data = []
        labels = []

        for i in range(7):
            date = current_date - timedelta(days=i)
            start_of_day = datetime(date.year, date.month, date.day)
            end_of_day = start_of_day + timedelta(days=1)
            
            count = db.users.count_documents({
                "last_login": {
                    "$gte": start_of_day,
                    "$lt": end_of_day
                }
            })
            
            labels.insert(0, date.strftime("%d %b"))
            daily_data.insert(0, count)

        return {
            "labels": labels,
            "values": daily_data
        }
