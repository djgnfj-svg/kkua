import { devtools } from 'zustand/middleware'
import { create } from 'zustand'

// persist 미들웨어 제거하고 메모리에만 상태 유지
const guestStore = create(
  devtools(
    (set) => ({
      uuid: null,
      nickname: null,
      guest_id: null,
      setGuestInfo: (guestInfo) => {
        console.log("guestStore setGuestInfo 호출:", guestInfo);
        set(guestInfo);
      },
      clearGuestInfo: () => {
        console.log("guestStore clearGuestInfo 호출");
        set({ uuid: null, guest_id: null, nickname: null });
      },
    })
  )
)

// 개발용 디버깅: 상태 변경 감지
if (process.env.NODE_ENV === 'development') {
  guestStore.subscribe((state) => {
    console.log('guestStore 상태 변경:', state);
  });
}

export default guestStore
