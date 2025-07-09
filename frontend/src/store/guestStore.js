import { create } from 'zustand';
import { persist } from 'zustand/middleware';

const guestStore = create(
  persist(
    (set) => ({
      uuid: null,
      nickname: '',
      guest_id: null,
      guest_uuid: null,
      setGuestInfo: ({ uuid, nickname, guest_id, guest_uuid }) =>
        set(() => ({
          uuid,
          nickname,
          guest_id,
          guest_uuid,
        })),
      resetGuestInfo: () =>
        set(() => ({
          uuid: null,
          nickname: '',
          guest_id: null,
          guest_uuid: null,
        })),
    }),
    {
      name: 'guest-storage',
      getStorage: () => localStorage,
      partialize: (state) => ({
        uuid: state.uuid,
        nickname: state.nickname,
        guest_id: state.guest_id,
        guest_uuid: state.guest_uuid,
      }),
    }
  )
);

export default guestStore;
