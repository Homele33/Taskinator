describe('Login Test', () => {
  beforeEach(() => {
    // Intercept both the OPTIONS preflight and the GET request
    cy.intercept('OPTIONS', '/api/tasks', {
      statusCode: 200,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization'
      },
      body: {} // Empty response for OPTIONS request
    }).as('optionsTasks');



    // Log in and visit the page
    cy.visit('/login');
    cy.get('[data-testid="email-input"]').type('test@example.com');
    cy.get('[data-testid="password-input"]').type('password123');
    cy.get('[data-testid="login-button"]').click();
  });

  it('should display tasks after login', () => {
    cy.wait('@optionsTasks');

    cy.location("href").should("eq", Cypress.config().baseUrl + "/")
    cy.get('[data-testid^="task-list"]').should("be.visible")
  });

});

describe("Logout Test", () => {
  beforeEach(() => {
    cy.intercept('OPTIONS', '/api/tasks', {
      statusCode: 200,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization'
      },
      body: {} // Empty response for OPTIONS request
    });

    cy.visit("/")
  })
  it("should be logged out", () => {
    cy.get('[data-testid="burger-menu"]').click()
    cy.get('[data-testid="logout-button"]').click()

    cy.location("href").should("include", '/login')

  })

})
