import React, { useState, useEffect, useRef } from 'react';

const slides = [
  { color: `rgb(175, 142, 235)` },
  { color: `rgb(241, 69, 79)` },
  { color: `rgb(163, 235, 142)` },
  { color: `rgb(46, 45, 213)` },
  { color: `rgb(213, 128, 45)` },
];

const Banner = () => {
  const [activeIndex, setActiveIndex] = useState(0);
  const intervalRef = useRef(null);

  const resetInterval = () => {
    if (intervalRef.current) clearInterval(intervalRef.current);

    intervalRef.current = setInterval(() => {
      setActiveIndex((prevIndex) => (prevIndex + 1) % slides.length);
    }, 3000);
  };

  useEffect(() => {
    resetInterval();
    return () => clearInterval(intervalRef.current);
  }, []);

  const handlePrevSlide = () => {
    setActiveIndex((prevIndex) =>
      prevIndex === 0 ? slides.length - 1 : prevIndex - 1
    );
    resetInterval();
  };

  const handleNextSlide = () => {
    setActiveIndex((prevIndex) => (prevIndex + 1) % slides.length);
    resetInterval();
  };

  const handleDotClick = (index) => {
    setActiveIndex(index);
    resetInterval();
  };

  if (window.innerWidth >= 768) {
    return null; // Desktop view doesn't show the banner
  }

  return (
    <div
      className="relative w-full h-[30vh] mt-5 flex items-center justify-center transition-all duration-500"
      style={{ backgroundColor: slides[activeIndex].color }}
    >
      <button
        onClick={handlePrevSlide}
        className="absolute left-2 bg-gray-300 text-black w-8 h-8 rounded-full shadow-md"
      ></button>
      <button
        onClick={handleNextSlide}
        className="absolute right-2 bg-gray-300 text-black w-8 h-8 rounded-full shadow-md"
      ></button>

      <div className="absolute bottom-2 flex space-x-2">
        {slides.map((_, index) => (
          <div
            key={index}
            onClick={() => handleDotClick(index)}
            className={`w-2 h-2 rounded-full cursor-pointer ${
              activeIndex === index ? 'bg-white' : 'bg-gray-400'
            }`}
          ></div>
        ))}
      </div>
    </div>
  );
};

export default Banner;
