function InGame() {
    return (
      <div className="min-h-screen bg-white p-4 flex flex-col items-center space-y-4">
        <h1 className="text-2xl font-bold">120초</h1>
        <div className="w-full max-w-md p-4 border-4 border-orange-400 rounded-lg text-center font-bold">
          콤보콤보콤보
        </div>
  
        <div className="w-full max-w-md space-y-2">
          <div className="p-2 rounded-lg border shadow flex items-center space-x-2">
            <div className="w-4 h-4 bg-red-400 rounded-full"></div>
            <span className="text-red-500 font-bold">넘뛰기</span>
          </div>
          <div className="p-2 rounded-lg border shadow flex items-center space-x-2">
            <div className="w-4 h-4 bg-orange-400 rounded-full"></div>
            <span className="text-orange-500 font-bold">터널</span>
          </div>
          <div className="p-2 rounded-lg border shadow flex items-center space-x-2">
            <div className="w-4 h-4 bg-yellow-400 rounded-full"></div>
            <span className="text-yellow-500 font-bold">햄스터</span>
          </div>
        </div>
  
        <div className="w-full max-w-md h-4 bg-gray-200 rounded-lg overflow-hidden">
          <div className="h-full bg-orange-400 w-1/4 relative">
            <div className="absolute top-0 -right-2 w-6 h-6 bg-white border border-orange-400 rounded-full">
              🐾
            </div>
          </div>
        </div>
  
        <div className="grid grid-cols-2 gap-4 w-full max-w-md">
          <div className="p-4 rounded-lg bg-gray-200 text-center font-bold">하양두유</div>
          <div className="p-4 rounded-lg border-4 border-orange-400 text-center font-bold">부러</div>
          <div className="p-4 rounded-lg bg-gray-200 text-center font-bold">김밥</div>
          <div className="p-4 rounded-lg bg-gray-200 text-center font-bold">후러</div>
        </div>
  
        <div className="w-full max-w-md flex items-center space-x-2 border-t pt-2">
          <span className="font-bold">⬆️</span>
          <input
            type="text"
            className="flex-1 p-2 border rounded-lg focus:outline-none"
            placeholder="기미"
          />
        </div>
      </div>
    );
  }
  
  export default InGame;
  