#include <algorithm>
#include <iostream>

#include "connectivity_octree.h"

namespace Geometry
{

    void clusterSingleMolecule(std::map<int, std::set<int>> &bonds, std::set<int> &currentCluster, int atomIndex)
    {
        auto cit = currentCluster.find(atomIndex);
        if (cit == currentCluster.end())
            currentCluster.insert(atomIndex);

        auto mit = bonds.find(atomIndex);
        auto bondedAtoms = mit->second;
        bonds.erase(mit);
        for (auto bondedAtom : bondedAtoms)
        {
            auto it = bonds.find(bondedAtom);
            if (it == bonds.end())
                continue;
            clusterSingleMolecule(bonds, currentCluster, bondedAtom);
        }
    }

    std::vector<std::set<int>> clusterMolecules(std::map<int, std::set<int>> &bonds)
    {
        std::vector<std::set<int>> clusters;
        while (!bonds.empty())
        {
            std::set<int> currentCluster;
            auto atomIndex = bonds.begin()->first;
            clusterSingleMolecule(bonds, currentCluster, atomIndex);
            clusters.push_back(currentCluster);
        }
        return clusters;
    }

    std::vector<int> ConnectivityOctree::powers = {1, 2, 4};

    ConnectivityOctree::ConnectivityOctree()
    {
    }

    ConnectivityOctree::ConnectivityOctree(const Eigen::Vector3d &lowerBound, const Eigen::Vector3d &upperBound)
        : _lowerBound(lowerBound),
          _upperBound(upperBound),
          _depth(0),
          _maxStorage(10),
          _maxDepth(8),
          _children()
    {
    }

    ConnectivityOctree::ConnectivityOctree(const Eigen::Vector3d &lowerBound, const Eigen::Vector3d &upperBound, int depth, int maXStorage, int maxDepth)
        : _lowerBound(lowerBound),
          _upperBound(upperBound),
          _depth(depth),
          _maxStorage(10),
          _maxDepth(8),
          _children()
    {
    }

    bool ConnectivityOctree::collide(const Eigen::Vector3d &lowerBound, const Eigen::Vector3d &upperBound) const
    {
        for (int i = 0; i < 3; ++i)
        {
            if (_upperBound(i) < lowerBound(i) || _lowerBound(i) > upperBound(i))
                return false;
        }
        return true;
    }

    bool ConnectivityOctree::hasChildren() const
    {
        return (!_children.empty());
    }

    void ConnectivityOctree::updateBoundingBox(int sector)
    {
        Eigen::Vector3d center = 0.5 * (_lowerBound + _upperBound);

        for (int i = 0; i < 3; ++i)
        {
            bool test = sector & powers[i];
            _lowerBound(i) = test ? center(i) : _lowerBound(i);
            _upperBound(i) = test ? _upperBound(i) : center(i);
        }
    }

    void ConnectivityOctree::split()
    {
        if (_depth > _maxDepth)
            return;

        _children.clear();

        for (int sector = 0; sector < 8; ++sector)
        {
            ConnectivityOctree childOctree(_lowerBound, _upperBound, _depth + 1, _maxStorage, _maxDepth);
            childOctree.updateBoundingBox(sector);
            _children.push_back(childOctree);
        }

        for (const auto &data : _data)
        {
            for (auto &child : _children)
                child.addPoint(data.index, data.point, data.radius);
        }

        _data.clear();
    }

    bool ConnectivityOctree::addPoint(int index, const Eigen::Vector3d &point, double radius)
    {
        Eigen::Vector3d extent = Eigen::Vector3d::Constant(radius);

        Eigen::Vector3d lb = point - extent;
        Eigen::Vector3d ub = point + extent;

        if (!collide(lb, ub))
            return false;

        if (hasChildren())
        {
            for (auto &child : _children)
                child.addPoint(index, point, radius);
        }
        else
        {
            _data.push_back({index, point, radius});
            if (_data.size() > static_cast<size_t>(_maxStorage))
                split();
        }

        return true;
    }

    void ConnectivityOctree::getData(std::set<Data> &data) const
    {
        if (hasChildren())
        {
            for (const auto &child : _children)
                child.getData(data);
        }
        else
        {
            for (const auto &d : _data)
                data.insert(d);
        }
    }

    void ConnectivityOctree::addIsolatedAtoms(std::map<int, std::set<int>> &collisions) const
    {
        std::set<Data> data;
        getData(data);

        std::set<int> firstSet;
        for (const auto &d : data)
            firstSet.insert(d.index);

        std::set<int> secondSet;
        for (const auto &col : collisions)
            secondSet.insert(col.first);

        std::set<int> diff;

        std::set_difference(firstSet.begin(), firstSet.end(), secondSet.begin(), secondSet.end(), std::inserter(diff, diff.begin()));

        for (auto v : diff)
            collisions.emplace(v, std::set<int>());
    }

    void ConnectivityOctree::getCollisions(std::map<int, std::set<int>> &collisions, double tolerance) const
    {
        if (hasChildren())
        {
            for (const auto &child : _children)
                child.getCollisions(collisions, tolerance);
        }
        else
        {
            if (_data.empty())
                return;

            auto nData = _data.size();
            for (size_t i = 0; i < nData - 1; ++i)
            {
                const auto &datai = _data[i];
                for (size_t j = i + 1; j < nData; ++j)
                {
                    const auto &dataj = _data[j];
                    auto iti = collisions.find(datai.index);
                    if (iti != collisions.end())
                    {
                        auto itj = std::find(iti->second.begin(), iti->second.end(), dataj.index);
                        if (itj != iti->second.end())
                            continue;
                    }

                    auto squaredDist = (datai.point - dataj.point).squaredNorm();
                    auto bond = (datai.radius + dataj.radius + tolerance);
                    auto squaredBond = bond * bond;
                    if (squaredDist <= squaredBond)
                    {
                        if (iti == collisions.end())
                            collisions.emplace(datai.index, std::set<int>({dataj.index}));
                        else
                            collisions.at(datai.index).insert(dataj.index);

                        auto itj = collisions.find(dataj.index);
                        if (itj == collisions.end())
                            collisions.emplace(dataj.index, std::set<int>({datai.index}));
                        else
                            collisions.at(dataj.index).insert(datai.index);
                    }
                }
            }
        }
    }

    void ConnectivityOctree::findCollisions(std::map<int, std::set<int>> &collisions, double tolerance) const
    {
        getCollisions(collisions, tolerance);
        addIsolatedAtoms(collisions);
    }

} // namespace Geometry