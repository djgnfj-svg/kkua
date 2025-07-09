// 표준화된 에러 메시지 관리
export const ERROR_MESSAGES = {
  // 네트워크 에러
  NETWORK_ERROR: '네트워크 연결을 확인해주세요.',
  SERVER_ERROR: '서버에 문제가 발생했습니다. 잠시 후 다시 시도해주세요.',
  TIMEOUT_ERROR: '요청 시간이 초과되었습니다. 다시 시도해주세요.',
  
  // 인증 에러
  AUTH_REQUIRED: '로그인이 필요합니다.',
  AUTH_FAILED: '로그인에 실패했습니다.',
  SESSION_EXPIRED: '세션이 만료되었습니다. 다시 로그인해주세요.',
  
  // 방 관련 에러
  ROOM_CREATE_FAILED: '방 생성에 실패했습니다. 다시 시도해주세요.',
  ROOM_JOIN_FAILED: '방 입장에 실패했습니다. 다시 시도해주세요.',
  ROOM_FULL: '방이 가득 찼습니다.',
  ROOM_NOT_FOUND: '존재하지 않는 방입니다.',
  ROOM_ALREADY_STARTED: '이미 시작된 게임입니다.',
  
  // 유효성 검사 에러
  INVALID_ROOM_TITLE: '방 제목은 2-20자 사이여야 합니다.',
  INVALID_NICKNAME: '닉네임은 2-10자 사이여야 합니다.',
  
  // 일반 에러
  UNKNOWN_ERROR: '알 수 없는 오류가 발생했습니다.',
  TRY_AGAIN: '다시 시도해주세요.',
};

// 에러 응답에서 메시지 추출
export const getErrorMessage = (error) => {
  // API 응답에서 에러 메시지 추출
  if (error.response?.data?.detail) {
    return error.response.data.detail;
  }
  
  if (error.response?.data?.message) {
    return error.response.data.message;
  }
  
  // HTTP 상태 코드별 메시지
  if (error.response?.status) {
    switch (error.response.status) {
      case 400:
        return '잘못된 요청입니다.';
      case 401:
        return ERROR_MESSAGES.AUTH_REQUIRED;
      case 403:
        return '권한이 없습니다.';
      case 404:
        return '요청한 리소스를 찾을 수 없습니다.';
      case 409:
        return '이미 존재하거나 충돌하는 요청입니다.';
      case 422:
        return '입력 데이터를 확인해주세요.';
      case 500:
        return ERROR_MESSAGES.SERVER_ERROR;
      case 502:
      case 503:
      case 504:
        return '서버가 일시적으로 이용할 수 없습니다.';
      default:
        return ERROR_MESSAGES.UNKNOWN_ERROR;
    }
  }
  
  // 네트워크 에러
  if (error.code === 'NETWORK_ERROR' || error.message === 'Network Error') {
    return ERROR_MESSAGES.NETWORK_ERROR;
  }
  
  // 타임아웃 에러
  if (error.code === 'ECONNABORTED') {
    return ERROR_MESSAGES.TIMEOUT_ERROR;
  }
  
  return error.message || ERROR_MESSAGES.UNKNOWN_ERROR;
};

// 성공 메시지
export const SUCCESS_MESSAGES = {
  ROOM_CREATED: '방이 성공적으로 생성되었습니다!',
  ROOM_JOINED: '방에 성공적으로 입장했습니다!',
  PROFILE_UPDATED: '프로필이 업데이트되었습니다!',
  LOGIN_SUCCESS: '로그인되었습니다!',
};