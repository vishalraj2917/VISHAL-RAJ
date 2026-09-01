import React, { useState } from 'react';
import { User, Mail, Shield, KeyRound, CheckCircle2, AlertCircle, Save } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { updateUserProfile, changeUserPassword } from '../services/api';

export const ProfileModal = ({ isOpen, onClose }) => {
  const { user, updateUser } = useAuth();
  const [name, setName] = useState(user?.name || '');
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmNewPassword, setConfirmNewPassword] = useState('');
  const [profileMsg, setProfileMsg] = useState(null);
  const [passwordMsg, setPasswordMsg] = useState(null);
  const [errorMsg, setErrorMsg] = useState(null);
  const [isUpdating, setIsUpdating] = useState(false);

  if (!isOpen || !user) return null;

  const handleUpdateProfile = async (e) => {
    e.preventDefault();
    setErrorMsg(null);
    setProfileMsg(null);
    setIsUpdating(true);
    try {
      const updated = await updateUserProfile(name);
      updateUser(updated);
      setProfileMsg('Profile updated successfully.');
    } catch (err) {
      setErrorMsg(err.response?.data?.detail || 'Failed to update profile.');
    } finally {
      setIsUpdating(false);
    }
  };

  const handleChangePassword = async (e) => {
    e.preventDefault();
    setErrorMsg(null);
    setPasswordMsg(null);

    if (newPassword !== confirmNewPassword) {
      setErrorMsg('New password and confirmation do not match.');
      return;
    }

    setIsUpdating(true);
    try {
      await changeUserPassword(currentPassword, newPassword, confirmNewPassword);
      setPasswordMsg('Password changed successfully.');
      setCurrentPassword('');
      setNewPassword('');
      setConfirmNewPassword('');
    } catch (err) {
      setErrorMsg(err.response?.data?.detail || 'Failed to change password.');
    } finally {
      setIsUpdating(false);
    }
  };

  return (
    <div className="modal-backdrop" style={{
      position: 'fixed',
      inset: 0,
      background: 'rgba(10, 15, 30, 0.8)',
      backdropFilter: 'blur(8px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 9999,
      padding: '1rem',
    }}>
      <div className="glass-card" style={{ maxWidth: '500px', width: '100%', padding: '2rem', maxHeight: '90vh', overflowY: 'auto' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <div className="ai-badge-icon" style={{ background: 'linear-gradient(135deg, var(--accent-violet), var(--accent-cyan))' }}>
              <User size={18} />
            </div>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 700, margin: 0 }}>Account Settings</h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            style={{ background: 'none', border: 'none', color: 'var(--text-muted)', fontSize: '1.5rem', cursor: 'pointer' }}
          >
            &times;
          </button>
        </div>

        {errorMsg && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            padding: '0.75rem',
            borderRadius: 'var(--radius-sm)',
            background: 'rgba(239, 68, 68, 0.15)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            color: 'var(--accent-rose)',
            fontSize: '0.85rem',
            marginBottom: '1rem',
          }}>
            <AlertCircle size={16} />
            <span>{errorMsg}</span>
          </div>
        )}

        {profileMsg && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            padding: '0.75rem',
            borderRadius: 'var(--radius-sm)',
            background: 'rgba(16, 185, 129, 0.15)',
            border: '1px solid rgba(16, 185, 129, 0.3)',
            color: 'var(--accent-emerald)',
            fontSize: '0.85rem',
            marginBottom: '1rem',
          }}>
            <CheckCircle2 size={16} />
            <span>{profileMsg}</span>
          </div>
        )}

        {/* Profile Details Form */}
        <form onSubmit={handleUpdateProfile} style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginBottom: '2rem' }}>
          <h3 style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--text-primary)', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.4rem', margin: 0 }}>
            Personal Information
          </h3>

          <div>
            <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.4rem' }}>
              Full Name
            </label>
            <input
              type="text"
              required
              className="input-field"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.4rem' }}>
              Email (Account Identity)
            </label>
            <input
              type="email"
              disabled
              className="input-field"
              style={{ opacity: 0.7, cursor: 'not-allowed' }}
              value={user.email}
            />
          </div>

          <button
            type="submit"
            disabled={isUpdating}
            className="btn-primary"
            style={{ justifyContent: 'center' }}
          >
            <Save size={16} />
            <span>Save Profile</span>
          </button>
        </form>

        {/* Change Password Form */}
        <form onSubmit={handleChangePassword} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <h3 style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--text-primary)', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.4rem', margin: 0 }}>
            Security & Password
          </h3>

          {passwordMsg && (
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              padding: '0.75rem',
              borderRadius: 'var(--radius-sm)',
              background: 'rgba(16, 185, 129, 0.15)',
              border: '1px solid rgba(16, 185, 129, 0.3)',
              color: 'var(--accent-emerald)',
              fontSize: '0.85rem',
            }}>
              <CheckCircle2 size={16} />
              <span>{passwordMsg}</span>
            </div>
          )}

          <div>
            <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.4rem' }}>
              Current Password
            </label>
            <input
              type="password"
              required
              className="input-field"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
            />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.4rem' }}>
              New Password (8+ chars, upper, lower, digit)
            </label>
            <input
              type="password"
              required
              className="input-field"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
            />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.4rem' }}>
              Confirm New Password
            </label>
            <input
              type="password"
              required
              className="input-field"
              value={confirmNewPassword}
              onChange={(e) => setConfirmNewPassword(e.target.value)}
            />
          </div>

          <button
            type="submit"
            disabled={isUpdating}
            className="btn-secondary"
            style={{ justifyContent: 'center' }}
          >
            <KeyRound size={16} />
            <span>Update Password</span>
          </button>
        </form>
      </div>
    </div>
  );
};
