describe("add nlp task", () => {
  before(() => {
    cy.login("test@example.com", "password123")
  })
  it('should create new task', () => {
    // input task text into nlp-input
    cy.get('[data-testid="nlp-input"]').type("testing nlp today at 13:00")
    cy.get('[data-testid="nlp-submit"]').click() // submit task 
    // make sure task is visiable
    cy.get('[data-testid="task-list"]').should("be.visible")

    // check the task for the right information
    cy.get('[data-testid^="task-title"]').should('contain.text', 'Test')
    cy.get('[data-testid^="task-status"]').should('contain.text', 'Todo')
  })

  it('should delete task', () => {
    // delete task from task-list
    cy.visit("/")
    cy.get('[data-testid^="task-menu"]').first().click()
    cy.get('[data-testid^="task-delete-button"]').first().click()

    cy.get('[data-testid^="task-list"]').should("be.visible")

  })
  after(() => {
    cy.logout()
  })
})
