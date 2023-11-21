// Mock data for cards
const cardsData = [
    {
      id: 1,
      imageUrl: "https://res.cloudinary.com/demo/image/upload/sample.jpg",
      specialties: "ART-THÉRAPIE",
      title: "Réflexologie de confort & Expression par le rythme",
      name: "Alice Larrabure",
      rating: 5,
      comments: 7
    },
    {
      id: 2,
      imageUrl: "https://res.cloudinary.com/demo/image/upload/sample.jpg",
      specialties: "Access Bars® <br> NATUROPATHIE <br> NUTRITION <br> PLANTES & HUILES ESSENTIELLES",
      title: "Réflexologie de confort",
      name: "Farah Benwahoud",
      rating: 4,
      comments: 20
    },
    {
      id: 3,
      imageUrl: "https://res.cloudinary.com/demo/image/upload/sample.jpg",
      specialties: "EMDR <br> PSYCHO-ÉNERGÉTIQUE <br> RESPIRATION HOLOTROPIQUE",
      title: "Fenêtre sur soi et créativité : Champ d'argile®, Soulcollage®",
      name: "Solange Lemoine",
      rating: 3,
      comments: 45
    },
    // ... add as many card objects as you need
  ];
  
  // Function to create the HTML for a star rating
  function getStarRatingHtml(rating) {
    let starsHtml = '';
    for (let i = 0; i < rating; i++) {
      starsHtml += '<svg width="10px" viewBox="0 0 20 20" fill="#FFD100">...</svg>';
    }
    for (let i = rating; i < 5; i++) {
      starsHtml += '<svg width="10px" viewBox="0 0 20 20" fill="#CCCCCC">...</svg>'; // Grey stars for missing ratings
    }
    return starsHtml;
  }
  
  // Function to create a card HTML element
  function createCardElement(card) {
    const cardHtml = `
      <div class="card-h">
        <div class="card-thumbnail">
          <img src="${card.imageUrl}">
          <div class="card-specialties">${card.specialties}</div>
        </div>
        <div class="card-body">
          <h3 class="card-title">${card.title}</h3>
          <div class="card-name">${card.name}</div>
        </div>
        <div class="card-foot">
          <div class="card-rating">
            ${getStarRatingHtml(card.rating)}
            ${card.comments} commentaires
          </div>
        </div>
      </div>
    `;
    return cardHtml;
  }
  
  // Function to render cards to the container
  function renderCards() {
    const cardsContainer = document.getElementById('cardsContainer');
    cardsData.forEach(card => {
      cardsContainer.innerHTML += createCardElement(card);
    });
  }
  
  // Call renderCards on script load
  renderCards();
  