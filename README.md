# Sorting Users into Groups Based on Ranked Preferences

## How to run it
-- update this later

## Learn how it works!

We can visualize an example the groups and preferences like so (we have 6 users who have ranked the groups best to worst, and 3 groups each with a capacity of 2):

<p align="center">
  <img src="https://github.com/user-attachments/assets/2c2e27e7-76e5-4084-a4d0-5078cae0c476">
</p>

Let's consider the situation with the group of users mentioned above. When we go through them one by one (in the order they are declared), the initial user assigned is John, who gets his first-choice group, Group 1. Here's what this implies: Jane and Olivia won't be able to have their first-choice group, and both of them dislike Group 2, which is the most readily available option. Consequently, either Jane or Olivia will have to settle for their least preferred choice.

<p align="center">
  <img src="https://github.com/cooper-ross/ranked-preference-sort/assets/120236631/efb3fe40-c84c-4d10-bc2d-46a5d26fd6b3">
</p>

Now, let's examine an alternative scenario where we prioritize Jane and Olivia over John in the assignment process. In this case, John would be placed in Group 2 instead of Group 1. The key difference here is that he now gets his second-choice group, which is a better outcome for him compared to his least preferred choice. This illustrates how the order in which we assign users to groups can significantly influence the overall results.

<p align="center">
  <img src="https://github.com/cooper-ross/ranked-preference-sort/assets/120236631/bbbf768a-95d1-4fc4-bdce-009837081574">
</p>

So now that we know that, how can we consider the impact of each choice to the final result? One method for visualizing and analyzing this impact is by using a directed graph (specifically a directed minimum-cost flow network), like the one I have below:

<p align="center">
  <img src="https://github.com/cooper-ross/ranked-preference-sort/assets/120236631/62addfb6-3973-4a9b-9a03-6bece0ac0a8e)">
</p>

Imagine we create a separate point (node) for each user and another point (node) for each group. We want to depict all the users and the choices they make. To do this, we use connections, like lines, to link each user to the group they prefer, and we assign a weight to these connections. For example, if John's favorite is Group 1, the connection from his node to the Group 1 node doesn't cost anything (it's free). On the other hand, if John ends up in his least favorite group, Group 3, that connection costs $2. These costs may seem somewhat arbitrary, but they actually reflect the order of preference for each user's choices.

If everyone was able to get into their favorite group, the total cost would be $0, which is great! But if one user got into their second choice group (the best possible outcome in this case), the cost would be $1. Keep in mind we can't assign more than two users to a group, since the edge capacity of the group to the Sink node (the destination) decreases for each user that goes down it, and stops any users if it has a capacity of 0 (think of it like a max uses or something).

This is really useful to us, since if we can figure out the lowest cost for each user's flow (see the -1 at the top? Imagine that's water trying to get to the Sink node at the bottom, and flowing down) to be allocated (and keep track of the path that got us there), we know that that sort is the most optimal sort possible!
