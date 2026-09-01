from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=True)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)
    last_login = Column(DateTime, nullable=True)

    predictions = relationship('Prediction', back_populates='user')
    alerts = relationship('Alert', back_populates='user')
    reports = relationship('Report', back_populates='user')


class Location(Base):
    __tablename__ = 'locations'

    id = Column(Integer, primary_key=True, index=True)
    city = Column(String(100), nullable=False, index=True)
    state = Column(String(100), nullable=True)
    country = Column(String(100), nullable=False, default='India')
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    created_at = Column(DateTime, default=utc_now)

    air_quality_records = relationship('AirQuality', back_populates='location')
    weather_records = relationship('Weather', back_populates='location')
    predictions = relationship('Prediction', back_populates='location')
    alerts = relationship('Alert', back_populates='location')


class AirQuality(Base):
    __tablename__ = 'air_quality'

    id = Column(Integer, primary_key=True, index=True)
    location_id = Column(Integer, ForeignKey('locations.id'), nullable=False, index=True)
    timestamp = Column(DateTime, default=utc_now, index=True, nullable=False)
    pm25 = Column(Float, nullable=True)
    pm10 = Column(Float, nullable=True)
    co = Column(Float, nullable=True)
    no2 = Column(Float, nullable=True)
    so2 = Column(Float, nullable=True)
    o3 = Column(Float, nullable=True)
    aqi = Column(Float, nullable=False, index=True)

    location = relationship('Location', back_populates='air_quality_records')


class Weather(Base):
    __tablename__ = 'weather'

    id = Column(Integer, primary_key=True, index=True)
    location_id = Column(Integer, ForeignKey('locations.id'), nullable=False, index=True)
    timestamp = Column(DateTime, default=utc_now, index=True, nullable=False)
    temperature = Column(Float, nullable=True)
    humidity = Column(Float, nullable=True)
    wind_speed = Column(Float, nullable=True)
    pressure = Column(Float, nullable=True)

    location = relationship('Location', back_populates='weather_records')


class Prediction(Base):
    __tablename__ = 'predictions'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True, index=True)
    location_id = Column(Integer, ForeignKey('locations.id'), nullable=False, index=True)
    prediction_time = Column(DateTime, nullable=False, index=True)
    predicted_aqi = Column(Float, nullable=False)
    model_name = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=utc_now)

    user = relationship('User', back_populates='predictions')
    location = relationship('Location', back_populates='predictions')


class Alert(Base):
    __tablename__ = 'alerts'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True, index=True)
    location_id = Column(Integer, ForeignKey('locations.id'), nullable=False, index=True)
    message = Column(Text, nullable=False)
    severity = Column(String(50), default='warning')
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utc_now)

    user = relationship('User', back_populates='alerts')
    location = relationship('Location', back_populates='alerts')


class Report(Base):
    __tablename__ = 'reports'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True, index=True)
    title = Column(String(200), nullable=False)
    summary = Column(Text, nullable=True)
    generated_at = Column(DateTime, default=utc_now)

    user = relationship('User', back_populates='reports')
