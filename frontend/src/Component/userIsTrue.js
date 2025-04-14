import guestStore from '../store/guestStore';
import axiosInstance from '../Api/axiosInstance';
import { USER_API } from '../Api/userApi';

async function userIsTrue() {
    const { uuid } = guestStore.getState();
    if(!uuid || uuid === 'undefined' ){
      return false;
    }else if (uuid) {
      try {
        const response = await axiosInstance.post(USER_API.GET_GUEST(uuid))
        console.log("클라이언트 uuid:", uuid)
        console.log("서버 응답:", response.data)

        if (response.data && response.data.uuid) {
          return true;
        }
      } catch (error) {
        console.warn("유효하지 않은 uuid, 새 게스트 생성 필요");
      }
    }
    return false;
}

export default userIsTrue;
