/*
export const USER_API = {
  GET_USER: '/api/user',
  CREATE_USER: '/api/user/create',
  UPDATE_USER: '/api/user/update',
};
*/
export const USER_API ={
  GET_GUEST : (guest_uuid) => `/guests/login?guest_uuid=${guest_uuid}`
}