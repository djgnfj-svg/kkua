import { devtools, persist } from 'zustand/middleware'
import {create} from 'zustand'

const guestStore = create(
  devtools(
    persist(
      (set) => ({
        uuid: null,
        nickname: null,
        guest_id: null,
        setGuestInfo: (data) => set(data),
        clearGuestInfo: () =>
          set({
            uuid: null,
            nickname: null,
            guest_id: null,
          }),
      }),
      {
        name: 'guest-storage', // localStorage key 이름
      }
    )
  )
)

const startButtonOn = async () => {
  const { uuid } = guestStore.getState();
  console.log("uuid = " + uuid);
}

export default guestStore
