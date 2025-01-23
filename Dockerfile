FROM mongo:5

# Copy the initialization script
COPY init-replica.js /init-replica.js

# Start MongoDB and initialize the replica set
CMD ["sh", "-c", "mongod --replSet myReplicaSet --bind_ip_all & sleep 5 && mongosh --file /init-replica.js"]
