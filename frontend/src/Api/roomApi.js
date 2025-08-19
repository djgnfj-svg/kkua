export const ROOM_API = {
  get_ROOMS: '/gamerooms/',
  CREATE_ROOMS: `/gamerooms/`,
  //rooms id값
  get_ROOMSID: (id) => `/gamerooms/${id}`,
  DELET_ROOMSID: (id) => `/gamerooms/${id}`,
  get_ROOMSUSER: (id) => `/gamerooms/${id}/participants`,
  JOIN_ROOMS: (id) => `/gamerooms/${id}/join`,
  LEAVE_ROOMS: (id) => `/gamerooms/${id}/leave`,
  PLAY_ROOMS: (id) => `/gamerooms/${id}/start`,
  END_ROOMS: (id) => `/gamerooms/${id}/end`,
  COMPLETE_ROOMS: (id) => `/gamerooms/${id}/complete`,
};
