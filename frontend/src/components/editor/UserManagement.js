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
  Globe,
} from 'lucide-react';
import { usersAPI, projectsAPI } from '../../lib/api';

const UserManagement = ({ onClose }) => {
  const [users, setUsers] = useState([]);
  const [projects, setProjects] = useState([]);
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
    project_access: [],
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

  const loadProjects = useCallback(async () => {
    try {
      const res = await projectsAPI.list();
      setProjects(res.data);
    } catch (err) {
      console.error('Failed to load projects:', err);
    }
  }, []);

  useEffect(() => {
    loadUsers();
    loadProjects();
  }, [loadUsers, loadProjects]);

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
      setFormData({ email: '', password: '', name: '', role: 'editor', project_access: [] });
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

  const handleProjectAccessChange = async (user, newProjectAccess) => {
    clearMessages();
    try {
      await usersAPI.update(user._id, { project_access: newProjectAccess });
      loadUsers();
      setSuccess('Project access updated');
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to update project access');
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

  const handleDelete = async (userId) => {
    if (!window.confirm('Are you sure you want to delete this user?')) return;
    clearMessages();
    try {
      await usersAPI.delete(userId);
      setSuccess('User deleted successfully');
      loadUsers();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to delete user');
    }
  };

  const toggleProjectAccess = (projectId) => {
    setFormData((prev) => ({
      ...prev,
      project_access: prev.project_access.includes(projectId)
        ? prev.project_access.filter((p) => p !== projectId)
        : [...prev.project_access, projectId],
    }));
  };

  const toggleProjectAccessForUser = (user, projectId) => {
    const currentAccess = user.project_access || [];
    const newAccess = currentAccess.includes(projectId)
      ? currentAccess.filter((p) => p !== projectId)
      : [...currentAccess, projectId];
    handleProjectAccessChange(user, newAccess);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="w-8 h-8 animate-spin" style={{ color: 'var(--primary)' }} />
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto custom-scrollbar" style={{ backgroundColor: 'var(--sunken)' }}>
      <div className="max-w-5xl mx-auto p-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-3">
            <div
              className="w-10 h-10 rounded-lg flex items-center justify-center"
              style={{ backgroundColor: 'var(--primary)', color: 'var(--bg)' }}
            >
              <UserCog className="w-5 h-5" />
            </div>
            <div>
              <h1 className="font-headline text-2xl font-bold" style={{ color: 'var(--on-surface)' }}>
                User Management
              </h1>
              <p className="text-sm" style={{ color: 'var(--muted)' }}>
                Manage users and their project access
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            data-testid="user-management-close-button"
            className="w-8 h-8 rounded-lg flex items-center justify-center transition-colors"
            style={{
              backgroundColor: 'var(--elevated)',
              color: 'var(--muted)',
            }}
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Messages */}
        <AnimatePresence>
          {error && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="mb-4 px-4 py-3 rounded-lg"
              style={{ backgroundColor: 'rgba(239, 68, 68, 0.1)', color: 'var(--danger)' }}
            >
              {error}
            </motion.div>
          )}
          {success && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="mb-4 px-4 py-3 rounded-lg"
              style={{ backgroundColor: 'rgba(16, 185, 129, 0.1)', color: 'var(--primary)' }}
            >
              {success}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Create User Button */}
        <div className="mb-6">
          <button
            onClick={() => setShowCreateForm(!showCreateForm)}
            data-testid="create-user-button"
            className="gradient-btn px-6 py-2.5 rounded-lg font-bold text-xs tracking-widest uppercase flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            Create New User
          </button>
        </div>

        {/* Create User Form */}
        <AnimatePresence>
          {showCreateForm && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="mb-6 p-6 rounded-lg"
              style={{ backgroundColor: 'var(--elevated)' }}
            >
              <h2 className="font-headline text-lg font-bold mb-4" style={{ color: 'var(--on-surface)' }}>
                Create New User
              </h2>
              <form onSubmit={handleCreate}>
                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div>
                    <label className="block text-xs font-medium mb-1.5" style={{ color: 'var(--muted)' }}>
                      EMAIL
                    </label>
                    <input
                      type="email"
                      data-testid="create-user-email"
                      value={formData.email}
                      onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                      className="w-full h-8 rounded-[4px] px-3 text-sm"
                      style={{
                        backgroundColor: 'var(--sunken)',
                        color: 'var(--on-surface)',
                        border: 'none',
                      }}
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium mb-1.5" style={{ color: 'var(--muted)' }}>
                      NAME
                    </label>
                    <input
                      type="text"
                      data-testid="create-user-name"
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      className="w-full h-8 rounded-[4px] px-3 text-sm"
                      style={{
                        backgroundColor: 'var(--sunken)',
                        color: 'var(--on-surface)',
                        border: 'none',
                      }}
                      required
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div>
                    <label className="block text-xs font-medium mb-1.5" style={{ color: 'var(--muted)' }}>
                      PASSWORD
                    </label>
                    <input
                      type="password"
                      data-testid="create-user-password"
                      value={formData.password}
                      onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                      className="w-full h-8 rounded-[4px] px-3 text-sm"
                      style={{
                        backgroundColor: 'var(--sunken)',
                        color: 'var(--on-surface)',
                        border: 'none',
                      }}
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium mb-1.5" style={{ color: 'var(--muted)' }}>
                      ROLE
                    </label>
                    <select
                      data-testid="create-user-role"
                      value={formData.role}
                      onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                      className="w-full h-8 rounded-[4px] px-3 text-sm"
                      style={{
                        backgroundColor: 'var(--sunken)',
                        color: 'var(--on-surface)',
                        border: 'none',
                      }}
                    >
                      <option value="editor">Editor</option>
                      <option value="admin">Admin</option>
                    </select>
                  </div>
                </div>

                {/* Project Access Selection */}
                {formData.role === 'editor' && projects.length > 0 && (
                  <div className="mb-4">
                    <label className="block text-xs font-medium mb-2" style={{ color: 'var(--muted)' }}>
                      PROJECT ACCESS
                    </label>
                    <div className="grid grid-cols-2 gap-2">
                      {projects.map((project) => (
                        <label
                          key={project.project_id}
                          className="flex items-center gap-2 p-2 rounded cursor-pointer transition-colors"
                          style={{
                            backgroundColor: formData.project_access.includes(project.project_id)
                              ? 'var(--primary-dim)'
                              : 'var(--sunken)',
                          }}
                        >
                          <input
                            type="checkbox"
                            checked={formData.project_access.includes(project.project_id)}
                            onChange={() => toggleProjectAccess(project.project_id)}
                            className="w-4 h-4"
                          />
                          <span className="text-sm" style={{ color: 'var(--on-surface)' }}>
                            {project.name}
                          </span>
                        </label>
                      ))}
                    </div>
                    {formData.role === 'editor' && formData.project_access.length === 0 && (
                      <p className="text-xs mt-1" style={{ color: 'var(--warning)' }}>
                        Editors without project access won't be able to access any projects
                      </p>
                    )}
                  </div>
                )}

                {formData.role === 'admin' && (
                  <div className="mb-4 p-3 rounded-lg" style={{ backgroundColor: 'var(--sunken)' }}>
                    <div className="flex items-center gap-2">
                      <Shield className="w-4 h-4" style={{ color: 'var(--primary)' }} />
                      <p className="text-xs" style={{ color: 'var(--muted)' }}>
                        Admins have access to all projects automatically
                      </p>
                    </div>
                  </div>
                )}

                <div className="flex gap-3">
                  <button type="submit" className="gradient-btn px-6 py-2 rounded-lg font-bold text-xs tracking-widest uppercase">
                    Create User
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowCreateForm(false)}
                    className="px-6 py-2 rounded-lg font-bold text-xs tracking-widest uppercase"
                    style={{ backgroundColor: 'var(--sunken)', color: 'var(--muted)' }}
                  >
                    Cancel
                  </button>
                </div>
              </form>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Users List */}
        <div className="space-y-3">
          {users.map((user) => (
            <div
              key={user._id}
              className="p-5 rounded-lg"
              style={{ backgroundColor: 'var(--elevated)' }}
              data-testid={`user-item-${user.email}`}
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div
                    className="w-10 h-10 rounded-full flex items-center justify-center font-bold"
                    style={{
                      backgroundColor: user.is_active ? 'var(--primary)' : 'var(--muted)',
                      color: 'var(--bg)',
                    }}
                  >
                    {user.name?.charAt(0)?.toUpperCase() || user.email.charAt(0).toUpperCase()}
                  </div>
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="font-headline font-bold" style={{ color: 'var(--on-surface)' }}>
                        {user.name || 'Unnamed'}
                      </h3>
                      <span
                        className="px-2 py-0.5 rounded text-[10px] font-bold tracking-widest uppercase"
                        style={{
                          backgroundColor: user.role === 'admin' ? 'var(--primary-dim)' : 'var(--sunken)',
                          color: user.role === 'admin' ? 'var(--primary)' : 'var(--muted)',
                        }}
                      >
                        {user.role}
                      </span>
                      {!user.is_active && (
                        <span
                          className="px-2 py-0.5 rounded text-[10px] font-bold tracking-widest uppercase"
                          style={{ backgroundColor: 'rgba(239, 68, 68, 0.1)', color: 'var(--danger)' }}
                        >
                          Disabled
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-1.5 text-sm" style={{ color: 'var(--muted)' }}>
                      <Mail className="w-3.5 h-3.5" />
                      {user.email}
                    </div>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleToggleActive(user)}
                    data-testid={`toggle-active-${user.email}`}
                    className="p-2 rounded hover:bg-opacity-80 transition-colors"
                    style={{ backgroundColor: 'var(--sunken)' }}
                    title={user.is_active ? 'Disable user' : 'Enable user'}
                  >
                    {user.is_active ? (
                      <ToggleRight className="w-4 h-4" style={{ color: 'var(--primary)' }} />
                    ) : (
                      <ToggleLeft className="w-4 h-4" style={{ color: 'var(--muted)' }} />
                    )}
                  </button>
                  <button
                    onClick={() => setEditingUser(editingUser === user._id ? null : user._id)}
                    data-testid={`edit-role-${user.email}`}
                    className="p-2 rounded hover:bg-opacity-80 transition-colors"
                    style={{ backgroundColor: 'var(--sunken)', color: 'var(--muted)' }}
                    title="Edit role"
                  >
                    <Edit3 className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => setChangingPassword(changingPassword === user._id ? null : user._id)}
                    data-testid={`change-password-${user.email}`}
                    className="p-2 rounded hover:bg-opacity-80 transition-colors"
                    style={{ backgroundColor: 'var(--sunken)', color: 'var(--muted)' }}
                    title="Change password"
                  >
                    <Key className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => handleDelete(user._id)}
                    data-testid={`delete-user-${user.email}`}
                    className="p-2 rounded hover:bg-opacity-80 transition-colors"
                    style={{ backgroundColor: 'var(--sunken)', color: 'var(--danger)' }}
                    title="Delete user"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {/* Project Access for Editors */}
              {user.role === 'editor' && projects.length > 0 && (
                <div className="mt-3 pt-3" style={{ borderTop: '1px solid var(--sunken)' }}>
                  <div className="flex items-center gap-2 mb-2">
                    <Globe className="w-3.5 h-3.5" style={{ color: 'var(--muted)' }} />
                    <label className="text-xs font-medium" style={{ color: 'var(--muted)' }}>
                      PROJECT ACCESS
                    </label>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {projects.map((project) => {
                      const hasAccess = (user.project_access || []).includes(project.project_id);
                      return (
                        <button
                          key={project.project_id}
                          onClick={() => toggleProjectAccessForUser(user, project.project_id)}
                          className="px-3 py-1.5 rounded text-xs font-medium transition-colors"
                          style={{
                            backgroundColor: hasAccess ? 'var(--primary-dim)' : 'var(--sunken)',
                            color: hasAccess ? 'var(--primary)' : 'var(--muted)',
                          }}
                        >
                          {hasAccess && <Check className="w-3 h-3 inline mr-1" />}
                          {project.name}
                        </button>
                      );
                    })}
                  </div>
                  {(!user.project_access || user.project_access.length === 0) && (
                    <p className="text-xs mt-2" style={{ color: 'var(--warning)' }}>
                      ⚠️ This editor has no project access
                    </p>
                  )}
                </div>
              )}

              {user.role === 'admin' && (
                <div className="mt-3 pt-3" style={{ borderTop: '1px solid var(--sunken)' }}>
                  <div className="flex items-center gap-2">
                    <Shield className="w-3.5 h-3.5" style={{ color: 'var(--primary)' }} />
                    <p className="text-xs" style={{ color: 'var(--muted)' }}>
                      Has access to all projects
                    </p>
                  </div>
                </div>
              )}

              {/* Role Change Form */}
              <AnimatePresence>
                {editingUser === user._id && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    className="mt-3 pt-3"
                    style={{ borderTop: '1px solid var(--sunken)' }}
                  >
                    <label className="block text-xs font-medium mb-2" style={{ color: 'var(--muted)' }}>
                      CHANGE ROLE
                    </label>
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleRoleChange(user, 'editor')}
                        className={`px-4 py-2 rounded text-xs font-bold tracking-widest uppercase ${
                          user.role === 'editor' ? 'gradient-btn' : ''
                        }`}
                        style={{
                          backgroundColor: user.role === 'editor' ? undefined : 'var(--sunken)',
                          color: user.role === 'editor' ? undefined : 'var(--muted)',
                        }}
                      >
                        Editor
                      </button>
                      <button
                        onClick={() => handleRoleChange(user, 'admin')}
                        className={`px-4 py-2 rounded text-xs font-bold tracking-widest uppercase ${
                          user.role === 'admin' ? 'gradient-btn' : ''
                        }`}
                        style={{
                          backgroundColor: user.role === 'admin' ? undefined : 'var(--sunken)',
                          color: user.role === 'admin' ? undefined : 'var(--muted)',
                        }}
                      >
                        Admin
                      </button>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Password Change Form */}
              <AnimatePresence>
                {changingPassword === user._id && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    className="mt-3 pt-3"
                    style={{ borderTop: '1px solid var(--sunken)' }}
                  >
                    <label className="block text-xs font-medium mb-2" style={{ color: 'var(--muted)' }}>
                      NEW PASSWORD
                    </label>
                    <div className="flex gap-2">
                      <input
                        type="password"
                        value={newPassword}
                        onChange={(e) => setNewPassword(e.target.value)}
                        placeholder="Enter new password"
                        className="flex-1 h-8 rounded-[4px] px-3 text-sm"
                        style={{
                          backgroundColor: 'var(--sunken)',
                          color: 'var(--on-surface)',
                          border: 'none',
                        }}
                      />
                      <button
                        onClick={() => handlePasswordChange(user._id)}
                        className="gradient-btn px-4 py-2 rounded text-xs font-bold tracking-widest uppercase"
                      >
                        Save
                      </button>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default UserManagement;
