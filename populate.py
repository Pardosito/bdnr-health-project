"""
For MongoDB, we plan to use a JSON file to populate our database since we believe it makes the most sense for this particular case.
Using mongoimport we can make a small script or function that will help us populate the database in case it is still empty.

For Cassandra, we plan to use a csv file to populate the database. We will have a small script or function that will run a for loop
reading and inserting all information.

For Dgraph, we also plan to use a JSON file since we also believe it makes the most sense to use that format. We will load it using
a small script or function using pydgraph to make sure everything is handled properly.

We are still debating whether to use an AI like ChatGPT or Gemini to generate the bulk data, which would allow us to have some control
over the generated data, or using a library like Faker to generate such bulk data.
"""