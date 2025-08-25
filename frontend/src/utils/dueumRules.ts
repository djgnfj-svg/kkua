/**
 * Korean Dueum Rules (두음법칙) Utility
 * Handles Korean initial sound change rules for frontend
 */

export interface DueumAlternatives {
  char: string;
  alternatives: string[];
}

export interface DueumValidationResult {
  isValid: boolean;
  validChars: string[];
  message?: string;
}

/**
 * Korean Dueum Rules Class
 */
export class DueumRules {
  // 두음법칙 매핑: 변환된 글자 → 원래 글자들
  private readonly dueumMappings: Record<string, string[]> = {
    // ㄴ으로 시작 (원래 ㄹ)
    '나': ['라'], '낙': ['락'], '난': ['란'], '날': ['랄'], '남': ['람'],
    '납': ['랍'], '낭': ['랑'], '내': ['래'], '냉': ['랭'], '녹': ['록'],
    '논': ['론'], '농': ['롱'], '뇌': ['뢰'], '누': ['루'], '능': ['릉'],
    '님': ['림'], '닙': ['립'], '노': ['로'], '뇽': ['룡'],
    
    // ㅇ으로 시작 (원래 ㄹ/ㄴ)
    '약': ['략'], '양': ['량'], '여': ['려', '녀'], '역': ['력', '녁'], 
    '연': ['련', '년'], '열': ['렬'], '염': ['렴', '념'], '엽': ['렵', '녑'], 
    '영': ['령', '녕'], '예': ['례'], '요': ['료', '뇨'], '용': ['룡'], 
    '유': ['류', '뉴'], '육': ['륙', '뉵'], '윤': ['륜'], '율': ['률'], 
    '융': ['륭'], '음': ['름'], '이': ['리', '니'], '인': ['린'], 
    '임': ['림'], '입': ['립'], '일': ['릴'], '익': ['릭'],
    
    // 추가 두음법칙 패턴
    '아': ['라'], '안': ['란'], '알': ['랄'], '암': ['람'], '압': ['랍'],
    '앙': ['랑'], '애': ['래'], '액': ['랙'], '앤': ['랜'], '앨': ['랠'],
    '앰': ['램'], '앱': ['랩'], '앵': ['랭'], '어': ['러'], '억': ['럭'],
    '언': ['런'], '얼': ['럴'], '엄': ['럼'], '업': ['럽'], '엉': ['렁'],
    '에': ['레'], '엑': ['렉'], '엔': ['렌'], '엘': ['렐'], '엠': ['렘'],
    '엡': ['렙'], '엥': ['렝'], '오': ['로'], '옥': ['록'], '온': ['론'],
    '올': ['롤'], '옴': ['롬'], '옵': ['롭'], '옹': ['롱'], '우': ['루'],
    '욱': ['룩'], '운': ['룬'], '울': ['룰'], '움': ['룸'], '웁': ['룹'],
    '웅': ['룽'], '워': ['뤄'], '원': ['뤈'], '월': ['뤌'], '위': ['뤼'],
    '은': ['른'], '을': ['를'], '읍': ['릅'],
  };

  // 역방향 매핑: 원래 글자 → 변환된 글자
  private reverseMappings: Record<string, string[]>;

  // 두음법칙 단어 예시
  private readonly dueumExamples: Record<string, string[]> = {
    '요리': ['료리', '뇨리'],
    '여행': ['려행', '녀행'],
    '역사': ['력사', '녁사'],
    '연구': ['련구', '년구'],
    '열정': ['렬정'],
    '영화': ['령화', '녕화'],
    '용기': ['룡기'],
    '유학': ['류학', '뉴학'],
    '음식': ['름식'],
    '이론': ['리론', '니론'],
    '인간': ['린간'],
    '나이': ['라이'],
    '남자': ['람자'],
    '농업': ['롱업'],
    '누나': ['루나'],
    '능력': ['릉력'],
  };

  constructor() {
    // 역방향 매핑 생성
    this.reverseMappings = {};
    for (const [converted, originals] of Object.entries(this.dueumMappings)) {
      for (const original of originals) {
        if (!this.reverseMappings[original]) {
          this.reverseMappings[original] = [];
        }
        this.reverseMappings[original].push(converted);
      }
    }
  }

  /**
   * 주어진 글자의 두음법칙 대안들을 반환
   */
  getDueumAlternatives(char: string): string[] {
    const alternatives: string[] = [];
    
    // 변환된 글자 → 원래 글자들
    if (char in this.dueumMappings) {
      alternatives.push(...this.dueumMappings[char]);
    }
      
    // 원래 글자 → 변환된 글자들  
    if (char in this.reverseMappings) {
      alternatives.push(...this.reverseMappings[char]);
    }
      
    return Array.from(new Set(alternatives));
  }

  /**
   * 단어가 두음법칙 적용 대상인지 확인
   */
  isDueumApplicable(word: string): boolean {
    if (!word || word.length < 1) return false;
    
    const firstChar = word[0];
    return firstChar in this.dueumMappings || firstChar in this.reverseMappings;
  }

  /**
   * 단어의 두음법칙 변형들을 생성
   */
  generateDueumVariants(word: string): string[] {
    if (!word) return [];
      
    const variants: string[] = [];
    const firstChar = word[0];
    const restOfWord = word.slice(1);
    
    const alternatives = this.getDueumAlternatives(firstChar);
    for (const altChar of alternatives) {
      const variant = altChar + restOfWord;
      variants.push(variant);
    }
      
    return variants;
  }

  /**
   * 입력된 단어가 목표 글자로 시작하는지 두음법칙을 고려하여 검사
   */
  checkWordValidity(inputWord: string, targetChar: string): DueumValidationResult {
    if (!inputWord || !targetChar) {
      return {
        isValid: false,
        validChars: [],
        message: '단어나 목표 글자가 없습니다'
      };
    }
      
    const firstChar = inputWord[0];
    
    // 직접 일치
    if (firstChar === targetChar) {
      return {
        isValid: true,
        validChars: [targetChar]
      };
    }
      
    // 두음법칙 검사
    const targetAlternatives = this.getDueumAlternatives(targetChar);
    const inputAlternatives = this.getDueumAlternatives(firstChar);
    
    // 목표 글자의 대안 중에 입력 글자가 있는지
    if (targetAlternatives.includes(firstChar)) {
      return {
        isValid: true,
        validChars: [targetChar, firstChar]
      };
    }
      
    // 입력 글자의 대안 중에 목표 글자가 있는지
    if (inputAlternatives.includes(targetChar)) {
      return {
        isValid: true,
        validChars: [targetChar, firstChar]
      };
    }
      
    // 서로의 대안들이 겹치는지
    const commonAlternatives = targetAlternatives.filter(alt => 
      inputAlternatives.includes(alt)
    );
    if (commonAlternatives.length > 0) {
      return {
        isValid: true,
        validChars: [targetChar, firstChar, ...commonAlternatives]
      };
    }
      
    return {
      isValid: false,
      validChars: [],
      message: `'${targetChar}'로 시작하는 단어여야 합니다`
    };
  }

  /**
   * UI 표시용 두음법칙 텍스트 생성
   */
  getDisplayText(char: string): string {
    const alternatives = this.getDueumAlternatives(char);
    if (alternatives.length > 0) {
      const mainAlt = alternatives[0]; // 주요 대안
      return `${char}(${mainAlt})`;
    }
    return char;
  }

  /**
   * 입력 도움말 텍스트 생성
   */
  getInputHelpText(char: string): string {
    const alternatives = this.getDueumAlternatives(char);
    if (alternatives.length > 0) {
      const altText = alternatives.slice(0, 2).join('/'); // 최대 2개 대안만 표시
      return `${char}(${altText})로 시작하는 단어`;
    }
    return `${char}로 시작하는 단어`;
  }

  /**
   * 두 글자가 두음법칙 관계인지 확인
   */
  isDueumPair(char1: string, char2: string): boolean {
    if (char1 === char2) return true;
      
    const alternatives1 = this.getDueumAlternatives(char1);
    const alternatives2 = this.getDueumAlternatives(char2);
    
    return alternatives1.includes(char2) || alternatives2.includes(char1);
  }

  /**
   * 비교를 위해 단어를 정규화 (모든 두음법칙 변형 포함)
   */
  normalizeForComparison(word: string): string[] {
    if (!word) return [];
      
    const normalized = [word]; // 원본 포함
    const variants = this.generateDueumVariants(word);
    normalized.push(...variants);
    
    return Array.from(new Set(normalized));
  }

  /**
   * 특정 글자로 시작할 수 있는 모든 두음법칙 글자들 반환
   */
  getAllPossibleStarts(char: string): Set<string> {
    const possibleStarts = new Set<string>([char]);
    const alternatives = this.getDueumAlternatives(char);
    alternatives.forEach(alt => possibleStarts.add(alt));
    return possibleStarts;
  }

  /**
   * 두음법칙 예시 단어들 반환
   */
  getExamples(): Record<string, string[]> {
    return { ...this.dueumExamples };
  }

  /**
   * 단어가 두음법칙 예시에 포함되어 있는지 확인
   */
  isExampleWord(word: string): boolean {
    return word in this.dueumExamples;
  }
}

// 전역 인스턴스
export const dueumRules = new DueumRules();

// 편의 함수들
export const getDueumAlternatives = (char: string): string[] => 
  dueumRules.getDueumAlternatives(char);

export const checkDueumWordValidity = (inputWord: string, targetChar: string): DueumValidationResult =>
  dueumRules.checkWordValidity(inputWord, targetChar);

export const getDueumDisplayText = (char: string): string =>
  dueumRules.getDisplayText(char);

export const getDueumInputHelp = (char: string): string =>
  dueumRules.getInputHelpText(char);

export const isDueumPair = (char1: string, char2: string): boolean =>
  dueumRules.isDueumPair(char1, char2);

export const generateDueumVariants = (word: string): string[] =>
  dueumRules.generateDueumVariants(word);

export default dueumRules;