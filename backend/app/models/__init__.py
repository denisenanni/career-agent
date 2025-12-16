from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Boolean, Float
from datetime import datetime

Base = declarative_base()

__all__ = ["Base", "Job", "User", "Match", "ScrapeLog", "SkillAnalysis"]

from app.models.job import Job
from app.models.user import User
from app.models.match import Match
from app.models.scrape_log import ScrapeLog
from app.models.skill_analysis import SkillAnalysis
