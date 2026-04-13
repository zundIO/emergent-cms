import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Users,
  Plus,
  Shield,
  Edit3,
  Trash2,
  X,
  Check,
  Loader2,
  Key,
  ToggleLeft,
  ToggleRight,
  UserCog,
  Mail,
} from 'lucide-react';
import { usersAPI } from '../../lib/api';

const UserManagement = ({ onClose }) => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [changingPassword, setChangingPassword] = useState(null);
  const [newPassword, setNewPassword] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // New user form
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    name: '',
    role: 'editor',
  });

  const loadUsers = useCallback(async () => {
    try {
      const res = await usersAPI.list();
      setUsers(res.data);
    } catch (err) {
      console.error('Failed to load users:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadUsers();
  }, [loadUsers]);

  const clearMessages = () => {
    setError('');
    setSuccess('');
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    clearMessages();
    try {
      await usersAPI.create(formData);
      setSuccess('User created successfully');
      setFormData({ email: '', password: '', name: '', role: 'editor' });
      setShowCreateForm(false);
      loadUsers();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create user');
    }
  };

  const handleToggleActive = async (user) => {
    clearMessages();
    try {
      await usersAPI.update(user._id, { is_active: !user.is_active });
      loadUsers();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to update user');
    }
  };

  const handleRoleChange = async (user, newRole) => {
    clearMessages();
    try {
      await usersAPI.update(user._id, { role: newRole });
      setEditingUser(null);
      loadUsers();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to change role');
    }
  };

  const handlePasswordChange = async (userId) => {
    if (!newPassword || newPassword.length < 4) {
      setError('Password must be at least 4 characters');
      return;
    }
    clearMessages();
    try {
      await usersAPI.changePassword(userId, newPassword);
      setSuccess('Password changed successfully');
      setChangingPassword(null);
      setNewPassword('');
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to change password');
    }
  };

  const handleDelete = async (user) => {
    clearMessages();
    if (!window.confirm(`Delete user ${user.email}? This action cannot be undone.`)) return;
    try {
      await usersAPI.delete(user._id);
      setSuccess('User deleted');
      loadUsers();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to delete user');
    }
  };

  return (
    <div className="p-6 md:p-10" data-testid="user-management-panel">
      <div className="max-w-[900px] mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h2
              className="font-headline text-2xl font-bold tracking-tight"
              style={{ color: 'var(--on-surface)' }}
            >
              User Management
            </h2>
            <p className="text-sm mt-1" style={{ color: 'var(--muted)' }}>
              Manage team members and their roles
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button
              data-testid="create-user-button"
              onClick={() => {
                setShowCreateForm(true);
                clearMessages();
              }}
              className="gradient-btn flex items-center gap-2 px-4 py-2 rounded-[4px] font-headline font-bold text-xs tracking-wider uppercase"
            >
              <Plus size={14} />
              Add User
            </button>
            {onClose && (
              <button
                onClick={onClose}
                className="w-8 h-8 rounded-[4px] grid place-items-center"
                style={{ color: 'var(--muted-2)' }}
              >
                <X size={16} />
              </button>
            )}
          </div>
        </div>

        {/* Messages */}
        <AnimatePresence>
          {error && (
            <motion.div
              initial={{ opacity: 0, y: -8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="mb-4 px-4 py-2 rounded-[4px] text-sm"
              style={{ backgroundColor: 'rgba(239, 68, 68, 0.1)', color: 'var(--danger)' }}
            >
              {error}
            </motion.div>
          )}
          {success && (
            <motion.div
              initial={{ opacity: 0, y: -8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="mb-4 px-4 py-2 rounded-[4px] text-sm"
              style={{ backgroundColor: 'rgba(16, 185, 129, 0.1)', color: 'var(--primary-2)' }}
            >
              {success}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Create User Form */}
        <AnimatePresence>
          {showCreateForm && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="overflow-hidden mb-6"
            >
              <form
                onSubmit={handleCreate}
                data-testid="create-user-form"
                className="p-6 rounded-[4px]"
                style={{ backgroundColor: 'var(--elevated)' }}
              >
                <h3 className="font-headline text-sm font-semibold mb-4" style={{ color: 'var(--on-surface)' }}>
                  New User
                </h3>
                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div>
                    <label className="block text-[10px] font-medium uppercase tracking-wider mb-1" style={{ color: 'var(--muted-2)' }}>
                      Name
                    </label>
                    <input
                      data-testid="create-user-name-input"
                      type="text"
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      className="w-full h-8 rounded-[4px] px-3 text-sm"
                      style={{ backgroundColor: 'var(--sunken)', color: 'var(--on-surface)', border: 'none', outline: 'none' }}
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-[10px] font-medium uppercase tracking-wider mb-1" style={{ color: 'var(--muted-2)' }}>
                      Email
                    </label>
                    <input
                      data-testid="create-user-email-input"
                      type="email"
                      value={formData.email}
                      onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                      className="w-full h-8 rounded-[4px] px-3 text-sm"
                      style={{ backgroundColor: 'var(--sunken)', color: 'var(--on-surface)', border: 'none', outline: 'none' }}
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-[10px] font-medium uppercase tracking-wider mb-1" style={{ color: 'var(--muted-2)' }}>
                      Password
                    </label>
                    <input
                      data-testid="create-user-password-input"
                      type="password"
                      value={formData.password}
                      onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                      className="w-full h-8 rounded-[4px] px-3 text-sm"
                      style={{ backgroundColor: 'var(--sunken)', color: 'var(--on-surface)', border: 'none', outline: 'none' }}
                      required
                      minLength={4}
                    />
                  </div>
                  <div>
                    <label className="block text-[10px] font-medium uppercase tracking-wider mb-1" style={{ color: 'var(--muted-2)' }}>
                      Role
                    </label>
                    <select
                      data-testid="create-user-role-select"
                      value={formData.role}
                      onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                      className="w-full h-8 rounded-[4px] px-3 text-sm appearance-none cursor-pointer"
                      style={{ backgroundColor: 'var(--sunken)', color: 'var(--on-surface)', border: 'none', outline: 'none' }}
                    >
                      <option value="editor">Editor</option>
                      <option value="admin">Admin</option>
                    </select>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <button
                    type="submit"
                    data-testid="create-user-submit"
                    className="gradient-btn flex items-center gap-1 px-4 py-2 rounded-[4px] font-headline font-bold text-xs tracking-wider uppercase"
                  >
                    <Check size={12} /> Create User
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowCreateForm(false)}
                    className="text-xs font-medium px-3 py-2 rounded-[4px]"
                    style={{ color: 'var(--muted)' }}
                  >
                    Cancel
                  </button>
                </div>
              </form>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Users list */}
        {loading ? (
          <div className="flex items-center justify-center py-16">
            <Loader2 size={20} className="animate-spin" style={{ color: 'var(--muted)' }} />
          </div>
        ) : (
          <div className="space-y-2">
            {users.map((user, idx) => (
              <motion.div
                key={user._id}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.04 }}
                data-testid={`user-row-${user.email}`}
                className="p-4 rounded-[4px] flex items-center gap-4"
                style={{ backgroundColor: 'rgba(255,255,255,0.02)' }}
              >
                {/* Avatar */}
                <div
                  className="w-10 h-10 rounded-full grid place-items-center text-sm font-bold flex-shrink-0"
                  style={{
                    backgroundColor: user.is_active !== false ? 'rgba(16, 185, 129, 0.14)' : 'rgba(239, 68, 68, 0.1)',
                    color: user.is_active !== false ? 'var(--primary-2)' : 'var(--danger)',
                  }}
                >
                  {user.name?.[0]?.toUpperCase() || user.email[0].toUpperCase()}
                </div>

                {/* Info */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-headline text-sm font-semibold" style={{ color: 'var(--on-surface)' }}>
                      {user.name}
                    </span>
                    {/* Role badge */}
                    {editingUser === user._id ? (
                      <select
                        data-testid={`user-role-select-${user.email}`}
                        value={user.role}
                        onChange={(e) => handleRoleChange(user, e.target.value)}
                        onBlur={() => setEditingUser(null)}
                        autoFocus
                        className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-[3px] appearance-none cursor-pointer"
                        style={{
                          backgroundColor: user.role === 'admin' ? 'rgba(56, 189, 248, 0.14)' : 'rgba(16, 185, 129, 0.14)',
                          color: user.role === 'admin' ? 'var(--info)' : 'var(--primary-2)',
                          border: 'none',
                          outline: 'none',
                        }}
                      >
                        <option value="admin">Admin</option>
                        <option value="editor">Editor</option>
                      </select>
                    ) : (
                      <span
                        className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-[3px] cursor-pointer"
                        onClick={() => setEditingUser(user._id)}
                        style={{
                          backgroundColor: user.role === 'admin' ? 'rgba(56, 189, 248, 0.14)' : 'rgba(16, 185, 129, 0.14)',
                          color: user.role === 'admin' ? 'var(--info)' : 'var(--primary-2)',
                        }}
                      >
                        {user.role === 'admin' ? 'Admin' : 'Editor'}
                      </span>
                    )}
                    {user.is_active === false && (
                      <span
                        className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-[3px]"
                        style={{ backgroundColor: 'rgba(239, 68, 68, 0.1)', color: 'var(--danger)' }}
                      >
                        Disabled
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-1 mt-0.5">
                    <Mail size={10} style={{ color: 'var(--muted-2)' }} />
                    <span className="text-xs" style={{ color: 'var(--muted-2)' }}>
                      {user.email}
                    </span>
                  </div>

                  {/* Inline password change */}
                  <AnimatePresence>
                    {changingPassword === user._id && (
                      <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        exit={{ opacity: 0, height: 0 }}
                        className="mt-2 flex items-center gap-2 overflow-hidden"
                      >
                        <input
                          data-testid={`password-input-${user.email}`}
                          type="password"
                          placeholder="New password"
                          value={newPassword}
                          onChange={(e) => setNewPassword(e.target.value)}
                          className="h-7 rounded-[4px] px-2 text-xs w-48"
                          style={{ backgroundColor: 'var(--sunken)', color: 'var(--on-surface)', border: 'none', outline: 'none' }}
                        />
                        <button
                          data-testid={`password-confirm-${user.email}`}
                          onClick={() => handlePasswordChange(user._id)}
                          className="w-7 h-7 rounded-[4px] grid place-items-center"
                          style={{ backgroundColor: 'rgba(16, 185, 129, 0.14)', color: 'var(--primary-2)' }}
                        >
                          <Check size={12} />
                        </button>
                        <button
                          onClick={() => { setChangingPassword(null); setNewPassword(''); }}
                          className="w-7 h-7 rounded-[4px] grid place-items-center"
                          style={{ color: 'var(--muted-2)' }}
                        >
                          <X size={12} />
                        </button>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-1 flex-shrink-0">
                  {/* Toggle active */}
                  <button
                    data-testid={`toggle-active-${user.email}`}
                    onClick={() => handleToggleActive(user)}
                    className="w-8 h-8 rounded-[4px] grid place-items-center transition-colors duration-150"
                    style={{ color: user.is_active !== false ? 'var(--primary-2)' : 'var(--muted-2)' }}
                    title={user.is_active !== false ? 'Disable user' : 'Enable user'}
                  >
                    {user.is_active !== false ? <ToggleRight size={18} /> : <ToggleLeft size={18} />}
                  </button>

                  {/* Change password */}
                  <button
                    data-testid={`change-password-${user.email}`}
                    onClick={() => {
                      setChangingPassword(changingPassword === user._id ? null : user._id);
                      setNewPassword('');
                      clearMessages();
                    }}
                    className="w-8 h-8 rounded-[4px] grid place-items-center transition-colors duration-150"
                    style={{ color: 'var(--muted)' }}
                    title="Change password"
                  >
                    <Key size={14} />
                  </button>

                  {/* Delete */}
                  <button
                    data-testid={`delete-user-${user.email}`}
                    onClick={() => handleDelete(user)}
                    className="w-8 h-8 rounded-[4px] grid place-items-center transition-colors duration-150"
                    style={{ color: 'var(--danger)' }}
                    title="Delete user"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default UserManagement;
