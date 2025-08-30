describe('Authentication test', () => {
  // Log in and visit the page
  it('should login', () => {
    cy.login();

    cy.location('href').should('not.include', '/login')
  })

  it('should display tasks after login', () => {
    cy.task_reload();
    cy.location("href").should("eq", Cypress.config().baseUrl + "/")
    cy.get('[data-testid^="task-list"]').should("be.visible")
  });

  it('should redirect on presist login', () => {
    cy.visit("login");

    cy.location('href').should('not.include', '/login')
  })

  it("should logout", () => {
    cy.logout();

    cy.location('href').should('include', '/login')
  })

});

