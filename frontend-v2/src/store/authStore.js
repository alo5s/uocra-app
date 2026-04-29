import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { authAPI } from '../api';

export const useAuthStore = create(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isAuthenticated: false,

      login: async (username, password) => {
        try {
          const response = await authAPI.login(username, password);
          const { access_token, user } = response.data;

          localStorage.setItem('token', access_token);
          set({ user, token: access_token, isAuthenticated: true });

          return { success: true };
        } catch (error) {
          return {
            success: false,
            message: error.response?.data?.detail || 'Error al iniciar sesión'
          };
        }
      },

      logout: () => {
        localStorage.removeItem('token');
        set({ user: null, token: null, isAuthenticated: false });
      },

      checkAuth: async () => {
        const token = localStorage.getItem('token');
        if (!token) {
          set({ isAuthenticated: false, user: null });
          return false;
        }

        try {
          const response = await authAPI.getMe();
          set({ user: response.data, isAuthenticated: true });
          return true;
        } catch (error) {
          localStorage.removeItem('token');
          set({ user: null, token: null, isAuthenticated: false });
          return false;
        }
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({ token: state.token, user: state.user }),
    }
  )
);