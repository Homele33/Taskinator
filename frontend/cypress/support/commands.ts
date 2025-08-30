Cypress.Commands.add("login", () => {
  const email = "test@example.com"
  const password = "password123"
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

Cypress.Commands.add("task_delete", () => {
  cy.intercept("DELETE", "api/tasks/*").as("deleteTask");

  cy.visit("/");
  cy.get('[data-testid^="task-menu"]').first().click();
  cy.get('[data-testid^="task-delete-button"]').first().click();

  cy.wait("@deleteTask");

})

Cypress.Commands.add("task_reload", () => {
  cy.intercept("GET", "/api/tasks").as("getTasks");

  cy.visit("/")
  cy.wait("@getTasks");
})
