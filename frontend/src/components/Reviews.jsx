import { useState, useRef } from "react";

import { Quote, Star } from 'lucide-react'; //icon pack xD

function Reviews() {

    const reviewRefs = useRef([]);

    const reviews = [
        {
            id: 1,
            name: "Alex Thompson",
            avatar: "https://i.pravatar.cc/100?img=1",
            rating: 5,
            review: "The AI-generated itinerary was perfect! Saved me hours of planning and found attractions I would have missed.",
            destination: "Tokyo",
        },
        {
            id: 2,
            name: "Samantha Lee",
            avatar: "https://i.pravatar.cc/100?img=5",
            rating: 5,
            review: "Incredible service that adapted to my family's preferences. The kids loved every activity recommended.",
            destination: "Orlando",
        },
        {
            id: 3,
            name: "Michael Rodriguez",
            avatar: "https://i.pravatar.cc/100?img=12",
            rating: 4,
            review: "Smart recommendations that considered local events. Got us into shows that were nearly sold out!",
            destination: "Barcelona",
        },
        {
            id: 4,
            name: "Emma Wilson",
            avatar: "https://i.pravatar.cc/100?img=9",
            rating: 5,
            review: "Flexible planning that adjusted when our flight was delayed. Couldn't have recovered our trip without it.",
            destination: "Paris",
        },
    ];

    return (
        <section className="review-section">
            <div className="container">
                <div className="text-center mb-16">
                    <div className="chip chip-secondary">
                        Traveler Experiences
                    </div>
                    <h2 className="section-title">
                        What Our Users Say
                    </h2>
                    <p className="section-description">
                        Real travelers share their experiences with our
                        AI-powered trip planning service
                    </p>
                </div>

                <div className="grid">
                    {reviews.map((review, index) => (
                        <div
                            key={review.id}
                            ref={(el) => (reviewRefs.current[index] = el)}
                            className="card hover-scale reveal"
                            style={{ transitionDelay: `${index * 150}ms` }}
                        >
                            <div className="flex-header">
                                <div className="user-info">
                                    <img
                                        src={review.avatar}
                                        alt={review.name}
                                        className="avatar"
                                        loading="lazy"
                                    />
                                    <div>
                                        <h3 className="user-name">
                                            {review.name}
                                        </h3>
                                        <p className="user-location">
                                            {review.destination}
                                        </p>
                                    </div>
                                </div>
                                <div className="quote-icon">
                                    <Quote className="w-6 h-6" />
                                </div>
                            </div>

                            <div className="star-rating">
                                {[...Array(5)].map((_, i) => (
                                    <Star
                                        key={i}
                                        className={`star ${i < review.rating ? "star-filled" : "star-empty"}`}
                                    />
                                ))}
                            </div>

                            <p className="review-text">
                                "{review.review}"
                            </p>
                        </div>
                    ))}
                </div>

                <div className="text-center mt-10">
                    <button className="btn-outline">See All Reviews</button>
                </div>
            </div>
        </section>
    );
}

export default Reviews;
