from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Boolean, Float
from datetime import datetime

Base = declarative_base()

__all__ = ["Base", "Job", "User", "Match", "ScrapeLog", "SkillAnalysis", "CustomSkill", "AllowedEmail", "UserJob"]

from app.models.job import Job
from app.models.user import User
from app.models.match import Match
from app.models.scrape_log import ScrapeLog
from app.models.skill_analysis import SkillAnalysis
from app.models.custom_skill import CustomSkill
from app.models.allowed_email import AllowedEmail
from app.models.user_job import UserJob
