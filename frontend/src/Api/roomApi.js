/*
export const POST_API = {
    GET_POSTS: '/api/posts',
    GET_POST_BY_ID: (id) => `/api/posts/${id}`,
    CREATE_POST: '/api/posts/create',
};
*/
export const ROOM_API = {
    get_ROOMS:'/gamerooms/',
    CREATE_ROOMS: (title,max_players,gamemode,time_limit) => `gamerooms/?title=${title}&max_players=${max_players}&game_mode=${gamemode}&time_limit=${time_limit}`,
    //rooms id값
    get_ROOMSID: (id) => `gamerooms/${id}`,
    JOIN_ROOMS : (id) => `gamerooms/${id}/join`,
    LEAVE_ROOMS : (id) => `gamerooms/${id}/leave`,
    PLAY_ROOMS : (id) => `gamerooms/${id}/play`,
    END_ROOMS : (id) => `gamerooms/${id}/end`
}
