/**
 * 브라우저 탭 간 통신을 위한 BroadcastChannel 유틸리티
 * 중복 연결 방지 및 탭 간 상태 동기화
 */

export interface TabMessage {
  type: 'CONNECTION_ESTABLISHED' | 'CONNECTION_REPLACED' | 'ROOM_JOINED' | 'ROOM_LEFT' | 'GAME_STATE_CHANGED';
  data: {
    userId?: number;
    roomId?: string;
    timestamp: string;
    tabId: string;
    [key: string]: any;
  };
}

class TabCommunicationManager {
  private channel: BroadcastChannel;
  private tabId: string;
  private currentUserId: number | null = null;
  private currentRoomId: string | null = null;
  private messageHandlers: Map<string, ((message: TabMessage) => void)[]> = new Map();

  constructor() {
    this.channel = new BroadcastChannel('kkua_game_channel');
    this.tabId = this.generateTabId();
    this.setupMessageListener();
  }

  private generateTabId(): string {
    return `tab_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  private setupMessageListener() {
    this.channel.onmessage = (event: MessageEvent<TabMessage>) => {
      const message = event.data;
      
      // 자신이 보낸 메시지는 무시
      if (message.data.tabId === this.tabId) {
        return;
      }

      console.log('📡 탭 간 메시지 수신:', message);

      // 메시지 타입별 핸들러 실행
      const handlers = this.messageHandlers.get(message.type) || [];
      handlers.forEach(handler => {
        try {
          handler(message);
        } catch (error) {
          console.error('탭 메시지 핸들러 오류:', error);
        }
      });
    };
  }

  // 메시지 전송
  public sendMessage(type: TabMessage['type'], data: Omit<TabMessage['data'], 'timestamp' | 'tabId'>) {
    const message: TabMessage = {
      type,
      data: {
        ...data,
        timestamp: new Date().toISOString(),
        tabId: this.tabId
      }
    };

    console.log('📤 탭 간 메시지 전송:', message);
    this.channel.postMessage(message);
  }

  // 메시지 핸들러 등록
  public onMessage(type: TabMessage['type'], handler: (message: TabMessage) => void) {
    if (!this.messageHandlers.has(type)) {
      this.messageHandlers.set(type, []);
    }
    this.messageHandlers.get(type)!.push(handler);
  }

  // 메시지 핸들러 제거
  public offMessage(type: TabMessage['type'], handler: (message: TabMessage) => void) {
    const handlers = this.messageHandlers.get(type);
    if (handlers) {
      const index = handlers.indexOf(handler);
      if (index > -1) {
        handlers.splice(index, 1);
      }
    }
  }

  // 현재 사용자 설정
  public setCurrentUser(userId: number) {
    this.currentUserId = userId;
    this.sendMessage('CONNECTION_ESTABLISHED', { userId });
  }

  // 방 참가 알림
  public notifyRoomJoined(roomId: string) {
    this.currentRoomId = roomId;
    this.sendMessage('ROOM_JOINED', { 
      userId: this.currentUserId!, 
      roomId 
    });
  }

  // 방 나가기 알림
  public notifyRoomLeft(roomId: string) {
    this.currentRoomId = null;
    this.sendMessage('ROOM_LEFT', { 
      userId: this.currentUserId!, 
      roomId 
    });
  }

  // 게임 상태 변경 알림
  public notifyGameStateChanged(gameState: any) {
    if (this.currentRoomId) {
      this.sendMessage('GAME_STATE_CHANGED', {
        userId: this.currentUserId!,
        roomId: this.currentRoomId,
        gameState
      });
    }
  }

  // 정리
  public destroy() {
    this.channel.close();
    this.messageHandlers.clear();
  }

  // 현재 탭 ID 반환
  public getTabId(): string {
    return this.tabId;
  }
}

// 싱글톤 인스턴스
let tabCommManager: TabCommunicationManager | null = null;

export const getTabCommunicationManager = (): TabCommunicationManager => {
  if (!tabCommManager) {
    tabCommManager = new TabCommunicationManager();
  }
  return tabCommManager;
};

export const destroyTabCommunicationManager = () => {
  if (tabCommManager) {
    tabCommManager.destroy();
    tabCommManager = null;
  }
};

export default TabCommunicationManager;