Cypress.Commands.add("login", (email: string, password: string) => {
  cy.visit("/login");
  cy.get('[data-testid="email-input"]').type(email);
  cy.get('[data-testid="password-input"]').type(password);
  cy.get('[data-testid="login-button"]').click();
});

Cypress.Commands.add("logout", () => {
  cy.intercept("GET", "/api/tasks").as("getTasks");

  cy.visit("/");
  cy.wait("@getTasks");

  cy.get('[data-testid="burger-menu"]').click();
  cy.get('[data-testid="logout-button"]').click();

});
