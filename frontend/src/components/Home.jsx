import { useState, useEffect, useCallback, useRef } from "react";

//  import

import "../styles/Home.css";

import {ArrowLeft, ArrowRight, Star, Quote, Heart} from "lucide-react";

const slideData = [
    {
        id: 1,
        title: "Discover Magical Theme Parks",
        description:
            "Let AI plan your perfect theme park adventure with optimized routes and minimal wait times.",
        image: "https://images.unsplash.com/photo-1503221043305-f7498f8b7888?ixlib=rb-4.0.3&auto=format&fit=crop&w=1200&q=80",
        color: "bg-gradient-1",
    },
    {
        id: 2,
        title: "Experience Local Culture",
        description:
            "Immerse yourself in authentic local experiences with AI-curated personalized itineraries.",
        image: "https://images.unsplash.com/photo-1507608869274-d3177c8bb4c7?q=80&w=2070&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
        color: "bg-gradient-2",
    },
    {
        id: 3,
        title: "Adventure Awaits",
        description:
            "From mountains to beaches, let our AI find the perfect destinations for your travel style.",
        image: "https://images.unsplash.com/photo-1530789253388-582c481c54b0?ixlib=rb-4.0.3&auto=format&fit=crop&w=1200&q=80",
        color: "bg-gradient-3",
    },
];

function Home() {
    const [currentSlide, setCurrentSlide] = useState(0);
    const [isChanging, setIsChanging] = useState(false);
    const [loaded, setLoaded] = useState([]);

    useEffect(() => {
        // Preload images
        slideData.forEach((slide, index) => {
            const img = new Image();
            img.src = slide.image;
            img.onload = () => {
                setLoaded((prev) => {
                    const newLoaded = [...prev];
                    newLoaded[index] = true;
                    return newLoaded;
                });
            };
        });
    }, []);

    const nextSlide = useCallback(() => {
        if (isChanging) return;

        setIsChanging(true);
        setTimeout(() => {
            setCurrentSlide((prev) =>
                prev === slideData.length - 1 ? 0 : prev + 1
            );
            setIsChanging(false);
        }, 500);
    }, [isChanging]);

    const prevSlide = useCallback(() => {
        if (isChanging) return;

        setIsChanging(true);
        setTimeout(() => {
            setCurrentSlide((prev) =>
                prev === 0 ? slideData.length - 1 : prev - 1
            );
            setIsChanging(false);
        }, 500);
    }, [isChanging]);

    useEffect(() => {
        const interval = setInterval(() => {
            nextSlide();
        }, 6000);

        return () => clearInterval(interval);
    }, [nextSlide]);

    return (
        <div className="main-container">
            <div className={`bg-gradient ${slideData[currentSlide].color}`}></div>

            <div className="container py-20 flex-row z-10">
                {/* Left content */}
                <div className={`left-content ${isChanging ? "opacity-0 translate-x-neg-10" : "opacity-100 translate-x-0"}`}>
                    <h1 className="container-title">
                        {slideData[currentSlide].title}
                    </h1>
                    <p className="container-description"> 
                        {slideData[currentSlide].description}
                    </p>
                    <div className="container-feature-buttons">
                        <button className="btn-primary"> Plan Your Trip </button>
                        <button className="btn-outline"> Learn More </button>
                    </div>
                </div>

                {/* Right content - image */}
                <div className="right-content">
                    <div className={`image-container ${isChanging ? "opacity-0 translate-x-10" : "opacity-100 translate-x-0"}`}>
                        {slideData.map((slide, index) => (
                            <div
                                key={slide.id}
                                className={`slide ${currentSlide === index ? "slide-active" : "slide-inactive"}`}
                            >
                                {loaded[index] && (
                                    <img
                                        src={slide.image}
                                        alt={slide.title}
                                        className="image-fade-in"
                                        loading="lazy"
                                    />
                                )}
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
}

export default Home;
