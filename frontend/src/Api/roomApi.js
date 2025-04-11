/*
export const POST_API = {
    GET_POSTS: '/api/posts',
    GET_POST_BY_ID: (id) => `/api/posts/${id}`,
    CREATE_POST: '/api/posts/create',
};
*/
export const ROOM_API = {
    get_ROOMS:'/gamerooms/',
    CREATE_ROOMS:'/gamerooms/',
    //rooms id값
<<<<<<< HEAD
    get_ROOMSID: (id) => `api/rooms/${id}`,
    JOIN_ROOMS : (id) => `api/rooms/${id}/join`,
    LEAVE_ROOMS : (id) => `api/rooms/${id}/leave`,
    PLAY_ROOMS : (id) => `api/rooms/${id}/play`,
    END_ROOMS : (id) => `api/rooms/${id}/end`
=======
    get_ROOMSID: (id) => `gamerooms/${id}`,
    JOIN_ROOMS : (id) => `gamerooms/${id}/join`,
    LEAVE_ROOMS : (id) => `gamerooms/${id}/leave`,
    PLAY_ROOMS : (id) => `gamerooms/${id}/play`,
    END_ROOMS : (id) => `gamerooms/${id}/end`
>>>>>>> feat_lobby_geust
}
