from sqlalchemy import Integer, String, ForeignKey, Float, Date, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from . import db

# class Politician(db.Model):
#     id: Mapped[int] = mapped_column(primary_key=True)
#     data_id: Mapped[str] = mapped_column(String, unique=True)
#     first_name: Mapped[str] = mapped_column(String)
#     last_name: Mapped[str] = mapped_column(String)

class Politician(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    candidate_id: Mapped[str] = mapped_column(String, unique=True)
    candidate_name: Mapped[str] = mapped_column(String)
    chamber: Mapped[str] = mapped_column(String) # Custom
    website_url: Mapped[str] = mapped_column(String, nullable=True)
    incumbent_challenger_indicator: Mapped[str] = mapped_column(String)
    political_party_affiliation: Mapped[str] = mapped_column(String)
    total_receipts: Mapped[float] = mapped_column(Float)
    debts_owed_by: Mapped[float] = mapped_column(Float)
    total_individual_contributions: Mapped[float] = mapped_column(Float)
    office_state: Mapped[str] = mapped_column(String)
    office_district: Mapped[str] = mapped_column(String)
    other_political_committee_contributions: Mapped[float] = mapped_column(Float)
    political_party_contributions: Mapped[float] = mapped_column(Float)
    coverage_end_date: Mapped[str] = mapped_column(String)
    individual_refunds: Mapped[float] = mapped_column(Float)
    committee_refunds: Mapped[float] = mapped_column(Float)
    percent_individual_contributions: Mapped[float] = mapped_column(Float)
    pac_contribution_percentage: Mapped[float] = mapped_column(Float)
    party_contribution_percentage: Mapped[float] = mapped_column(Float)
    adjusted_party_contributions: Mapped[float] = mapped_column(Float)
    adjusted_pac_contributions: Mapped[float] = mapped_column(Float)
    percent_individual: Mapped[float] = mapped_column(Float)
    funding_group: Mapped[str] = mapped_column(String)
    individual_percentile_all: Mapped[float] = mapped_column(Float)
    individual_percentile_bin: Mapped[str] = mapped_column(String)
    description_generated_at: Mapped[DateTime] = mapped_column(DateTime, nullable=True)
    description: Mapped[str] = mapped_column(String, nullable=True)

