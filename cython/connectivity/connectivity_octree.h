#pragma once

#include <map>
#include <set>
#include <vector>

#include <Eigen/Dense>

namespace Geometry
{

    struct Data
    {
        int index;
        Eigen::Vector3d point;
        double radius;
        bool operator<(const Data &other) const { return index < other.index; }
    };

    std::vector<std::set<int>> clusterMolecules(std::map<int, std::set<int>> &bonds);

    class ConnectivityOctree
    {
    public:
        ConnectivityOctree();

        ConnectivityOctree(const Eigen::Vector3d &lowerBound, const Eigen::Vector3d &upperBound);

        ConnectivityOctree(const Eigen::Vector3d &lowerBound, const Eigen::Vector3d &upperBound, int depth, int maxStorage, int maxDepth);

        bool addPoint(int index, const Eigen::Vector3d &point, double radius);

        void getNeighbour(const Eigen::Vector3d &point, int& index) const;

        void findCollisions(std::map<int, std::set<int>> &collisions, double tolerance = 1.0e-1) const;

        void getData(std::set<Data> &data) const;

    private:
        static std::vector<int> powers;

        bool hasChildren() const;

        bool collide(const Eigen::Vector3d &lowerBound, const Eigen::Vector3d &upperBound) const;

        bool contains(const Eigen::Vector3d &point) const;

        void updateBoundingBox(int sector);

        void getCollisions(std::map<int, std::set<int>> &collisions, double tolerance) const;

        void addIsolatedAtoms(std::map<int, std::set<int>> &collisions) const;

        void split();

    private:
        Eigen::Vector3d _lowerBound;

        Eigen::Vector3d _upperBound;

        int _depth;

        int _maxStorage;

        int _maxDepth;

        std::vector<ConnectivityOctree> _children;

        std::vector<Data> _data;
    };
} // namespace Geometry